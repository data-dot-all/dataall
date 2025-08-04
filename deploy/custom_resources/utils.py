import os

from aws_cdk import aws_lambda, BundlingOptions
from aws_cdk.aws_lambda import AssetCode

from stacks.solution_bundling import SolutionBundling
from stacks.runtime_options import PYTHON_LAMBDA_RUNTIME


def get_lambda_code(path, image=PYTHON_LAMBDA_RUNTIME.bundling_image) -> AssetCode:
    assets_path = os.path.realpath(
        os.path.join(
            os.path.dirname(__file__),
            path,
        )
    )

    return aws_lambda.Code.from_asset(
        path=assets_path,
        bundling=BundlingOptions(
            image=image,
            local=SolutionBundling(source_path=assets_path),
        ),
    )
