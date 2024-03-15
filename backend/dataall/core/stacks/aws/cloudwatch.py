import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import List

import boto3

log = logging.getLogger('aws:CloudWatch')


class QueryStatus(Enum):
    COMPLETE = 'Complete'
    FAILED = 'Failed'


class CloudWatch:
    def __init__(self):
        pass

    @staticmethod
    def run_query(query: str, log_group_name: str, days: int, timeout_min: int = 5) -> List[dict]:
        """
        Runs a query against a given log group name via Cloudwatch insights
        Args:
            query: the query to be run
            log_group_name: the log group to run the query against
            days: the number of days back to query
            timeout_min: the number of minutes before the query should be canceled
        """
        timeout = datetime.utcnow() + timedelta(minutes=timeout_min)
        query_id = CloudWatch.start_query(query, log_group_name, days)
        return CloudWatch.fetch_query_results(query_id, timeout)

    @staticmethod
    def start_query(query: str, log_group_name: str, days: int) -> str:
        """
        Starts a cloudwatch insights query
        Args:
            query: the query to be run
            log_group_name: the log group to run the query against
            days: the number of days back to query
        """
        client = boto3.client('logs')

        start_time = time.mktime((datetime.utcnow() - timedelta(days=days)).timetuple())
        end_time = time.time()

        query_response = client.start_query(
            logGroupName=log_group_name,
            startTime=round(start_time),
            endTime=round(end_time),
            queryString=query,
            limit=10000,
        )
        return query_response['queryId']

    @staticmethod
    def fetch_query_results(query_id: str, timeout: datetime) -> List[dict]:
        """
        Waits for and returns the results from a given cloudwatch insights
        query
        Args:
            query_id: the query id to fetch results for
            timeout: the time at which the query should be canceled/timed out
        """
        client = boto3.client('logs')

        results = None
        while datetime.utcnow() < timeout:
            time.sleep(2)
            results = client.get_query_results(queryId=query_id)
            if results['status'] in [
                QueryStatus.COMPLETE.value,
                QueryStatus.FAILED.value,
            ]:
                break

        results = [
            {
                r['field'].replace('@', ''): r['value']
                for r in records
                if (r['field'] in ['@message', '@timestamp', '@logStream', '@logGroup'])
            }
            for records in results['results']
        ]
        return results
