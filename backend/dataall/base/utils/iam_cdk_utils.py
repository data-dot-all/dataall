from typing import Dict, Any, List
from aws_cdk import aws_iam as iam

from dataall.base.utils.iam_policy_utils import split_policy_statements_in_chunks


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


def process_and_split_statements_in_chunks(statements: List[Dict]):
    statement_chunks_json = split_policy_statements_in_chunks(statements)
    statements_chunks = []
    for statement_js in statement_chunks_json:
        if not statement_js.get('Condition', None):
            statements_chunks.append(convert_from_json_to_iam_policy_statement_with_conditions(statement_js))
        else:
            statements_chunks.append(convert_from_json_to_iam_policy_statement(statement_js))
    return statements_chunks
