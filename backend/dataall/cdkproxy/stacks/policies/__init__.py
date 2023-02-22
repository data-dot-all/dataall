"""Contains the code for creating environment policies"""

from dataall.cdkproxy.stacks.policies import (
    _lambda, cloudformation, codestar, databrew, glue,
    lakeformation, quicksight, redshift, stepfunctions, data_policy, service_policy
)

#TODO : should go away after refactoring of ml studios
import dataall.modules.common.sagemaker.policies as sagemaker

__all__ = ["_lambda", "cloudformation", "codestar", "databrew", "glue", "lakeformation", "quicksight",
           "redshift", "stepfunctions", "data_policy", "service_policy", "sagemaker"]
