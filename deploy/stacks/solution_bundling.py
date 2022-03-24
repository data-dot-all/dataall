import subprocess
from pathlib import Path

import jsii
from aws_cdk import ILocalBundling, BundlingOptions


@jsii.implements(ILocalBundling)
class SolutionBundling:
    """This interface allows AWS Solutions to package lambda functions without the use of Docker"""

    def __init__(self, source_path=None):
        self.source_path = source_path

    def try_bundle(self, output_dir: str, options: BundlingOptions) -> bool:
        requirements_path = Path(self.source_path, 'requirements.txt')
        command = [
            f'cp -a {self.source_path}/. {output_dir}/ && pip install -r {requirements_path} -t {output_dir}'
        ]
        subprocess.check_output(
            command,
            stderr=subprocess.STDOUT,
            shell=True,
        )

        ls_output = subprocess.check_output(
            [f'ls -ll {output_dir}'],
            stderr=subprocess.STDOUT,
            shell=True,
        )
        return True
