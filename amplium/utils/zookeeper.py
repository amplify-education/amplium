"""Used for calling ZookeeperGridNodeStatus"""

import ast
import json
import re
import logging

from collections import defaultdict, Counter

import requests

from kazoo.client import KazooClient
from kazoo.handlers.threading import KazooTimeoutError

logger = logging.getLogger(__name__)


class ZookeeperGridNodeStatus(object):
    """Initializes the zookeeper and gets the nodes from zookeeper"""

    def __init__(self, nerve_directory, host=None, port=None):
        host = host
        port = port
        zookeeper_host = "%s:%s" % (host, port)
        self.zookeeper = KazooClient(hosts=zookeeper_host, read_only=True)
        self.nerve_directory = nerve_directory

    def get_nodes(self):
        """
        Gets the children

        Returns:
            array:   Returns an array with all the nodes with their data
        """
        try:
            self.zookeeper.start()
            ip_addresses = []
            children = self.zookeeper.get_children(self.nerve_directory)

            # Creates a json
            for child in children:
                # Gets host, port, and name
                host_data = self.get_grid_node_data(child)
                node_ip = self.build_url(host_data['host'], host_data['port'])

                # Gets the browser usage
                browsers = self.get_usage_per_browser_type(node_ip)
                host_data['browsers'] = browsers['breakdown']

                # Gets the total capacity
                host_data['total_capacity'] = self.get_grid_hub_sessions_capacity(node_ip)
                host_data['available_capacity'] = host_data['total_capacity'] - browsers['total']

                # Gets the queue
                response = requests.get(node_ip + "/grid/api/hub").json()
                host_data['queue'] = response['newSessionRequestCount']

                ip_addresses.append(host_data)

            self.zookeeper.stop()
            return ip_addresses
        except KazooTimeoutError:
            logger.exception("Zookeeper Timeout Error:")
            return []

    def get_grid_node_data(self, grid_node):
        """Gets host, port, and name from the grid node"""
        child_directory = "{0}/{1}".format(self.nerve_directory, grid_node)
        child_data = self.zookeeper.get(child_directory)
        # Gets host, port, and name
        return ast.literal_eval(child_data[0])

    def get_grid_hub_sessions_capacity(self, url):
        "Get max sessions capacity of the grid"
        hub_max_capacity = 0
        # get all max sessions info from each nodes configuration
        for node in self.get_all_registered_nodes_ip(url):
            data = {"id": node}
            response = requests.get(url + "/grid/api/proxy/", data=json.dumps(data)).json()
            hub_max_capacity += response["request"]["configuration"]["maxSession"]
        return hub_max_capacity

    def get_usage_per_browser_type(self, url):
        """Gets the browser for each grid node"""
        nodes = []
        browser_stats_dict = {}
        browser_nums = defaultdict(int)
        browser_versions = defaultdict(list)

        # Get all sessions info for each node in nodes list
        for node_ip in self.get_all_registered_nodes_ip(url):
            data = requests.get(node_ip + "/wd/hub/sessions/").json()
            nodes.append(data)

        # parse dictionary to get total browser type on each node
        for node in nodes:

            for browser in node['value']:
                try:
                    capabilities = browser['capabilities']
                    browser_name = capabilities['browserName']
                    browser_version = capabilities.get('browserVersion') or capabilities.get('version')
                    browser_nums[browser_name] += 1
                    browser_versions[browser_name].append(browser_version)
                except KeyError:
                    logger.exception(
                        'Capabilities object is weird: %s', capabilities or 'Could not get capabilities'
                    )

        browser_stats_dict['total'] = sum(browser_nums.values())
        browser_stats_dict["breakdown"] = {}
        for browser_type in browser_versions:
            browser_stats_dict["breakdown"][browser_type] = {
                'version': {versions_number: number for versions_number, number in
                            Counter(browser_versions[browser_type]).iteritems()}
            }
        return browser_stats_dict

    def get_all_registered_nodes_ip(self, url):
        "Get all ip of nodes registered to the selenium hub"
        html_content = requests.get(url + '/grid/console').content
        # get all ips from the html of the grid console
        nodes_ip_list = re.findall('id : (http://.+?:[0-9]{1,5})', html_content)
        return nodes_ip_list

    def build_url(self, host, port):
        """Builds the url based on the port number"""
        protocol = "http"
        if port == 443:
            protocol = "https"
        return "{0}://{1}:{2}".format(protocol, host, port)
