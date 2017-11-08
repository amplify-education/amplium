"""Class for handling grid state"""

import hashlib
import json
import re
import logging
from collections import defaultdict, Counter

from amplium.api.exceptions import NoAvailableGridsException, NoAvailableCapacityException
from amplium.utils.utils import retry

logger = logging.getLogger(__name__)


class GridHandler(object):
    """Class for handling grid state"""

    def __init__(self, config, zookeeper, datadog, saucelabs, session):
        self.hashes_to_grids = {}
        self.config = config
        self.zookeeper = zookeeper
        self.datadog = datadog
        self.saucelabs = saucelabs
        self.session = session

    def store_grid_url(self, url):
        """
        Stores a grid for later lookup using its hash.
        :param url: The URL of the grid.
        :return: The MD5 hash for later lookup of this grid.
        """
        generated_hash = hashlib.sha256(url).hexdigest()

        self.hashes_to_grids[generated_hash] = url

        return generated_hash

    def retrieve_grid_url(self, desired_hash):
        """
        Retrieves a grid URL by its hash.
        :param desired_hash: The unique hash of the grid.
        :return: The URL of that grid.
        """
        if desired_hash not in self.hashes_to_grids:
            for grid in self.zookeeper.get_nodes():
                self.store_grid_url(self._format_url(grid["host"], grid["port"]))
        return self.hashes_to_grids[desired_hash]

    def generate_session_id(self, session_id, grid_url):
        """
        Convenience function for generating our own session id on top of the Selenium Grid's session id.
        :param session_id: The original session id used by Selenium.
        :param grid_url: The URL of the Selenium Grid Hub.
        :return: A new unique session id.
        """
        grid_hash = self.store_grid_url(grid_url)
        return "{0}-{1}".format(session_id, grid_hash)

    def unroll_session_id(self, session_id):
        """
        Convenience function for unrolling our own session id and yielding the original session id used by
        Selenium as well as the Selenium Grid Hub's URL.
        :param session_id: Our own session id.
        :return: A tuple containing the original session id and the URL of the session's Selenium Grid Hub.
        """
        session_id_components = session_id.split("-")
        session_id = "-".join(session_id_components[:-1])
        grid_hash = session_id_components[-1]

        # Builds the url with the correct session id and the given command
        url = self.retrieve_grid_url(grid_hash)

        return session_id, url

    def get_base_url(self, session_request):
        """
        Determines the base URL that the given session should use.
        :param session_request: Dictionary representing the request for a new session
        :return: A URL to a Selenium Grid matching the session request.
        """
        # Look through the request keys for capabilities, because they might want to use SauceLabs
        for key, value in session_request.iteritems():
            if key.endswith('Capabilities'):
                # If SauceLabs is not used, use zookeeper to find the url
                if self.saucelabs.is_saucelabs_requested(value):
                    host_and_ip = retry(
                        func=self.saucelabs.get_sauce_url,
                        max_time=self.config.session_queue_time
                    )
                    return self._format_url(*host_and_ip)

        # If SauceLabs didn't yield a url, get a normal grid.
        host_and_ip = retry(
            func=self._get_selenium_grid,
            max_time=self.config.session_queue_time
        )

        return self._format_url(*host_and_ip)

    def _get_selenium_grid(self):
        """
        Function for getting a Selenium Grid Hub from Zookeeper.
        :return: Host and port of a Selenium Grid Hub as a tuple.
        """
        discovered_grids = self.get_grid_info()
        if not discovered_grids:
            raise NoAvailableGridsException("No grids are registered to Amplium")

        # Make sure all discovery grids are stored in the dictionary
        for grid in discovered_grids:
            self.store_grid_url(self._format_url(grid["host"], grid["port"]))

        nodes = sorted(
            [
                grid for grid in discovered_grids
                if grid['available_capacity'] > 0
            ],
            cmp=self._compare_node
        )

        if nodes:
            return nodes[0]['host'], nodes[0]['port']

        self.datadog.send(
            metric='amplium.queue_length',
            metric_type='counter',
            value=1
        )

        raise NoAvailableCapacityException("No available capacity on any grid")

    def _compare_node(self, node1, node2):
        """Sorts nodes based on lowest queue,highest total, and lowest available capacity"""
        compare_queue = node1['queue'] - node2['queue']
        if compare_queue != 0:
            return compare_queue

        compare_total = node1['total_capacity'] - node2['total_capacity']
        if compare_total != 0:
            # Note the inversion, because we want the LARGEST total capacity
            return -compare_total

        compare_available = node1['available_capacity'] - node2['available_capacity']
        return compare_available

    def _format_url(self, host, port):
        """Builds the url based on the port number"""
        protocol = "http"
        if int(port) == 443:
            protocol = "https"
        return "{0}://{1}:{2}".format(protocol, host, port)

    def get_grid_info(self):
        """
        Convenience function for compiling a list of grids available to Amplium and their capacity.
        :return: List of dictionaries.
        """
        nodes = self.zookeeper.get_nodes()
        data = []
        for node in nodes:
            host_data = {'host': node['host'], 'port': node['port']}
            node_ip = self._format_url(node['host'], node['port'])

            # Gets the browser usage
            browsers = self.get_usage_per_browser_type(node_ip)
            host_data['browsers'] = browsers['breakdown']

            # Gets the total capacity
            host_data['total_capacity'] = self.get_grid_hub_sessions_capacity(node_ip)
            host_data['available_capacity'] = host_data['total_capacity'] - browsers['total']

            # Gets the queue
            response = self.session.get(node_ip + "/grid/api/hub").json()
            host_data['queue'] = response['newSessionRequestCount']
            data.append(host_data)

        return data

    def get_all_registered_nodes_ip(self, url):
        "Get all ip of nodes registered to the selenium hub"
        html_content = self.session.get(url + '/grid/console').content
        # get all ips from the html of the grid console
        nodes_ip_list = re.findall('id : (http[s]?://.+?:[0-9]{1,5})', html_content)
        return nodes_ip_list

    def get_grid_hub_sessions_capacity(self, url):
        "Get max sessions capacity of the grid"
        hub_max_capacity = 0
        # get all max sessions info from each nodes configuration
        for node in self.get_all_registered_nodes_ip(url):
            data = {"id": node}
            response = self.session.get(url + "/grid/api/proxy/", data=json.dumps(data)).json()
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
            data = self.session.get(node_ip + "/wd/hub/sessions/").json()
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
