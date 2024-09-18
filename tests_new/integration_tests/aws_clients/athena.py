import time


class AthenaClient:
    def __init__(self, session, region):
        self._client = session.client('athena', region_name=region)
        self._region = region
        self.retries = 10
        self.timeout = 5

    def run_query(self, query, workgroup='primary', output_location=None):
        if output_location:
            result = self._client.start_query_execution(
                QueryString=query, ResultConfiguration={'OutputLocation': output_location}
            )
        else:
            result = self._client.start_query_execution(QueryString=query, WorkGroup=workgroup)
        return result['QueryExecutionId']

    def wait_for_query(self, query_id):
        for i in range(self.retries):
            result = self._client.get_query_execution(QueryExecutionId=query_id)
            state = result['QueryExecution']['Status']['State']
            if state not in ['QUEUED', 'RUNNING']:
                return state
            time.sleep(self.timeout)

    def list_work_groups(self):
        result = self._client.list_work_groups()
        return [x['Name'] for x in result['WorkGroups']]

    def get_env_work_group(self, env_name):
        workgroups = self.list_work_groups()
        for workgroup in workgroups:
            if env_name in workgroup:
                return workgroup
