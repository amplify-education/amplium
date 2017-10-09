"""Used for calling DynamoDBHandler"""

import time
import logging
import boto3
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)


class DynamoDBHandler(object):
    """Handles the dynamodb calls"""

    def __init__(self, table_name, region=None):
        """Initilizes the class"""
        dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = dynamodb.Table(table_name)
        logger.info("Using table: %s", table_name)

    def add_entry(self, session_id, base_url):
        """Creates a new entry to the table, returns false if error occurred"""
        try:
            # ttl_date is to to expire next day
            ttl_date = long(time.time() + 86400)
            self.table.put_item(
                Item={
                    'SessionId': session_id,
                    'BaseUrl': base_url,
                    'ttl': ttl_date
                }
            )
            logger.info("(%s, %s) added to table %s", session_id, base_url, self.table.name)
            return True
        except ClientError:
            logger.exception("Error occured creating new table entry: ")
            return False

    def delete_entry(self, session_id):
        """Deletes an entry from the table based on the session id, returns false if error occurred"""
        try:
            self.table.delete_item(
                Key={
                    'SessionId': session_id
                }
            )
            logger.info("Session Id %s has been removed from the table", session_id)
            return True
        except ClientError:
            logger.exception("Could not delete SessionId and BaseUrl from Table")
            return False

    def get_entry(self, session_id):
        """Returns the item based on the session id"""
        try:
            response = self.table.get_item(
                Key={
                    'SessionId': session_id
                }
            )
            return response['Item']
        except ClientError:
            logger.exception("Client Error Occured")
            return None
        except KeyError:
            logger.exception("Item does not exist")
            return None
