from typing import Dict, Any
from aws_cdk import aws_iam as iam


def convert_from_json_to_iam_policy_statement_with_conditions(iam_policy: Dict[Any, Any]):
    return iam.PolicyStatement(
        sid=iam_policy.get('Sid'),
        effect=iam_policy.get('Effect'),
        actions=iam_policy.get('Action'),
        resources=iam_policy.get('Resource'),
        conditions=iam_policy.get('Condition'),
    )


def convert_from_json_to_iam_policy_statement(iam_policy: Dict[Any, Any]):
    return iam.PolicyStatement(
        sid=iam_policy.get('Sid'),
        effect=iam_policy.get('Effect'),
        actions=iam_policy.get('Action'),
        resources=iam_policy.get('Resource'),
    )
