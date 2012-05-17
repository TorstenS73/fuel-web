import simplejson as json
from django import http
from django.test import TestCase

from nailgun.models import Node, Role


class TestHandlers(TestCase):

    def setUp(self):
        self.request = http.HttpRequest()
        self.old_meta = {'block_device': 'value',
                         'interfaces': 'val2',
                         'cpu': 'asf',
                         'memory': 'sd'
                        }
        self.node_name = "test.server.com"

        self.node = Node(environment_id=1,
                    name=self.node_name,
                    metadata=self.old_meta)
        self.node.save()
        self.role = Role()
        self.role.name = "myrole"
        self.role.save()
        
        self.node.roles = [self.role]
        self.node.save()
        self.node_url = '/api/environments/1/nodes/' + self.node_name

        self.new_meta = {'block_device': 'new-val',
                         'interfaces': 'd',
                         'cpu': 'u',
                         'memory': 'a'
                        }
        self.meta_json = json.dumps(self.new_meta)

    def tearDown(self):
        self.node.delete()
        self.role.delete()

    def test_create_new_entry_for_node(self):
        url = '/api/environments/1/nodes/new-node.test.com'
        resp = self.client.put(url, json.dumps(self.new_meta), "application/json")
        self.assertEquals(resp.status_code, 200)

        nodes_from_db = Node.objects.filter(environment_id=1,
                                            name='new-node.test.com')
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, self.new_meta)

    def test_node_valid_metadata_gets_updated(self):
        resp = self.client.put(self.node_url, json.dumps(self.new_meta), "application/json")
        self.assertEquals(resp.status_code, 200)

        nodes_from_db = Node.objects.filter(environment_id=1,
                                            name=self.node_name)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, self.new_meta)

    def test_put_returns_400_if_no_body(self):
        resp = self.client.put(self.node_url, None, "application/json")
        self.assertEquals(resp.status_code, 400)

    def test_put_returns_400_if_wrong_content_type(self):
        resp = self.client.put(self.node_url, self.meta_json, "plain/text")
        self.assertEquals(resp.status_code, 400)

    def test_put_returns_400_if_no_name(self):
        url = '/api/environments/1/nodes/'
        resp = self.client.put(url, self.meta_json, "application/json")
        self.assertEquals(resp.status_code, 400)

    def test_put_returns_400_if_no_block_device_attr(self):
        meta = self.new_meta.copy()
        del meta['block_device']
        resp = self.client.put(self.node_url, json.dumps(meta), "application/json")
        self.assertEquals(resp.status_code, 400)

        nodes_from_db = Node.objects.filter(environment_id=1,
                                            name=self.node_name)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, self.old_meta)

    def test_put_returns_400_if_no_interfaces_attr(self):
        meta = self.new_meta.copy()
        del meta['interfaces']
        resp = self.client.put(self.node_url, json.dumps(meta), "application/json")
        self.assertEquals(resp.status_code, 400)

        nodes_from_db = Node.objects.filter(environment_id=1,
                                            name=self.node_name)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, self.old_meta)

    def test_put_returns_400_if_no_cpu_attr(self):
        meta = self.new_meta.copy()
        del meta['cpu']
        resp = self.client.put(self.node_url, json.dumps(meta), "application/json")
        self.assertEquals(resp.status_code, 400)

        nodes_from_db = Node.objects.filter(environment_id=1,
                                            name=self.node_name)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, self.old_meta)

    def test_put_returns_400_if_no_memory_attr(self):
        meta = self.new_meta.copy()
        del meta['memory']
        resp = self.client.put(self.node_url, json.dumps(meta), "application/json")
        self.assertEquals(resp.status_code, 400)

        nodes_from_db = Node.objects.filter(environment_id=1,
                                            name=self.node_name)
        self.assertEquals(len(nodes_from_db), 1)
        self.assertEquals(nodes_from_db[0].metadata, self.old_meta)

    def test_put_on_nodes_does_not_modify_roles_list(self):
        resp = self.client.put(self.node_url, json.dumps(self.new_meta),
                "application/json")

        nodes_from_db = Node.objects.filter(environment_id=1,
                                            name=self.node_name)
        self.assertEquals(nodes_from_db[0].roles.all()[0].name, "myrole")


    # Tests for RoleHandler
    def test_can_get_list_of_roles_for_node(self):
        resp = self.client.get(self.node_url + '/roles')
        self.assertEquals(json.loads(resp.content)[0]['name'], 'myrole')

    def test_list_of_roles_gets_updated_via_put_on_roles(self):
        roles = [{'name': 'role1'}, {'name': 'role2'}]
        resp = self.client.put(self.node_url + '/roles', json.dumps(roles),
                "application/json")

        roles_from_db = Role.objects.all()
        self.assertEquals(roles_from_db[1].name, 'role1')
        self.assertEquals(roles_from_db[2].name, 'role2')

        nodes_from_db = Node.objects.filter(environment_id=1,
                                            name=self.node_name)
        self.assertEquals(nodes_from_db[0].roles.all()[0].name, "myrole")
        self.assertEquals(nodes_from_db[0].roles.all()[1].name, "role1")
        self.assertEquals(nodes_from_db[0].roles.all()[2].name, "role2")
