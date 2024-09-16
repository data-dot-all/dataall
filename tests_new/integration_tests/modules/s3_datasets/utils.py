from tests_new.integration_tests.modules.s3_datasets.aws_clients import S3Client
from tests_new.integration_tests.utils import poller


@poller(check_success=lambda resp: resp is not None, timeout=600)
def check_access_point_exists(client, account, region, access_point_name):
    s3_client = S3Client(session=client, region=region)
    return s3_client.get_access_point(account, access_point_name)
