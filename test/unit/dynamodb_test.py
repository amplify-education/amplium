"""Unit testing for dynamodb.py"""

import unittest
import time
import decimal
import boto3
from amplium.utils import dynamodb_handler
from moto import mock_dynamodb2
from mock import patch, MagicMock

session_id = 'test_session'
base_url = 'http://test_host:1234'
table_name = 'test_table'

current_time = int(time.time())


def create_table():
    """Creates a mock table"""
    dynamodb = boto3.resource('dynamodb')
    dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'SessionId',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'SessionId',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'ttl',
                'AttributeType': 'N'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )


class DyanmoDBUnitTests(unittest.TestCase):
    """Unit tests for dynamodb_handler.py"""

    @patch('time.time', MagicMock(return_value=current_time))
    @mock_dynamodb2
    def test_add_entry(self):
        """Tests the add entry method"""
        create_table()

        dynamodb_mock = dynamodb_handler.DynamoDBHandler(table_name)
        dynamodb_mock.add_entry(session_id, base_url)

        response = dynamodb_mock.get_entry(session_id)
        self.assertEqual(response, {'SessionId': 'test_session',
                                    'BaseUrl': 'http://test_host:1234',
                                    'ttl': decimal.Decimal(current_time + 86400)})

    @mock_dynamodb2
    def test_add_entry_fail(self):
        """Tests if add entry fails"""
        dynamodb_mock = dynamodb_handler.DynamoDBHandler(table_name)
        response = dynamodb_mock.add_entry(session_id, base_url)
        self.assertEqual(response, False)

    @mock_dynamodb2
    def test_delete_entry(self):
        """Tests delete entry """
        create_table()
        dynamodb_mock = dynamodb_handler.DynamoDBHandler(table_name)
        dynamodb_mock.add_entry(session_id, base_url)
        dynamodb_mock.delete_entry(session_id)
        response = dynamodb_mock.get_entry(session_id)
        self.assertEqual(response, None)

    @mock_dynamodb2
    def test_delete_entry_fail(self):
        """Tests if delete entry fails"""
        create_table()
        dynamodb_mock = dynamodb_handler.DynamoDBHandler(table_name)
        response = dynamodb_mock.delete_entry(session_id)
        self.assertEqual(response, False)
