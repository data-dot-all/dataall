import os
import logging
import shutil
from aws_cdk import aws_s3_deployment

from dataall.core.environment.cdk.environment_stack import EnvironmentSetup, EnvironmentStackExtension

log = logging.getLogger(__name__)


class DatasetGlueProfilerExtension(EnvironmentStackExtension):
    """Extends an environment stack for glue profiler"""

    @staticmethod
    def extent(setup: EnvironmentSetup):
        asset_path = DatasetGlueProfilerExtension.get_path_to_asset()
        profiling_assetspath = DatasetGlueProfilerExtension.zip_code(asset_path)

        aws_s3_deployment.BucketDeployment(
            setup,
            f'{setup.environment().resourcePrefix}GlueProflingJobDeployment',
            sources=[aws_s3_deployment.Source.asset(profiling_assetspath)],
            destination_bucket=setup.default_environment_bucket,
            destination_key_prefix='profiling/code',
        )

    @staticmethod
    def get_path_to_asset():
        return os.path.realpath(os.path.abspath(os.path.join(__file__, '..', 'assets', 'glueprofilingjob')))

    @staticmethod
    def zip_code(assets_path, s3_key='profiler'):
        log.info('Zipping code')
        shutil.make_archive(base_name=f'{assets_path}/{s3_key}', format='zip', root_dir=f'{assets_path}')
        return assets_path
