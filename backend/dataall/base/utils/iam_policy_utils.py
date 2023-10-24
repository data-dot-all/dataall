from typing import List
import logging
from aws_cdk import aws_iam as iam

logger = logging.getLogger(__name__)

POLICY_LIMIT = 6144
POLICY_HEADERS_BUFFER = 144  # The policy headers take around 60 chars. An extra buffer of 84 chars is added for any additional spacing or char that is unaccounted.
MAXIMUM_NUMBER_MANAGED_POLICIES = 20  # Soft limit 10, hard limit 20


def split_policy_statements_in_chunks(statements: List):
    """
    Splitter used for IAM policies with an undefined number of statements
    - Ensures that the size of the IAM policy remains below the POLICY LIMIT
    - If it exceeds the POLICY LIMIT, it breaks the policy into multiple policies (chunks)
    - Note the POLICY_HEADERS_BUFFER to account for the headers of the policy which usually take around ~60chars
    """
    chunks = []
    index = 0
    statements_list_of_strings = [str(s.to_json()) for s in statements]
    total_length = len(', '.join(statements_list_of_strings))
    logger.info(f"Number of statements = {len(statements)}")
    logger.info(f"Total length of statements = {total_length}")
    max_length = max(statements_list_of_strings, key=len)
    if len(max_length) > POLICY_LIMIT - POLICY_HEADERS_BUFFER:
        raise Exception(f"Policy statement {max_length} exceeds maximum policy size")
    while index < len(statements):
        #  Iterating until all statements are assigned to a chunk.
        #  "index" represents the statement position in the statements list
        chunk = []
        chunk_size = 0
        while index < len(statements) and chunk_size + len(str(statements[index].to_json())) < POLICY_LIMIT - POLICY_HEADERS_BUFFER:
            #  Appends a statement to the chunk until we reach its maximum size.
            #  It compares, current size of the statements < allowed size for the statements section of a policy
            chunk.append(statements[index])
            chunk_size += len(str(statements[index].to_json()))
            index += 1
        chunks.append(chunk)
    logger.info(f"Total number of managed policies = {len(chunks)}")
    if len(chunks) > MAXIMUM_NUMBER_MANAGED_POLICIES:
        raise Exception("The number of policies calculated exceeds the allowed maximum number of managed policies")
    return chunks


def split_policy_with_resources_in_statements(base_sid, effect, actions, resources):
    """
    Splitter used for IAM policy statements with an undefined number of resources.
    - Ensures that the size of the IAM statement is below the POLICY LIMIT
    - If it exceeds the POLICY LIMIT, it breaks the statement in multiple statements with a subset of resources
    - Note the POLICY_HEADERS_BUFFER to account for the headers of the policy which usually take around ~60chars
    """
    statement_without_resources = iam.PolicyStatement(
        sid=base_sid,
        effect=effect,
        actions=actions,
        resources=["*"]
    )
    resources_str = '" ," '.join(r for r in resources)
    number_resources = len(resources)
    max_length = len(max(resources, key=len))
    base_length = len(str(statement_without_resources.to_json()))
    total_length = base_length + len(resources_str)
    logger.info(f"Policy base length = {base_length}")
    logger.info(f"Number of resources = {number_resources}, resource maximum length = {max_length}")
    logger.info(f"Resources as string length = {len(resources_str)}")
    logger.info(f"Total length approximated as base length + resources string length = {total_length}")

    if total_length < POLICY_LIMIT - POLICY_HEADERS_BUFFER:
        logger.info("Not exceeding policy limit, returning statement ...")
        resulting_statement = iam.PolicyStatement(
            sid=base_sid,
            effect=effect,
            actions=actions,
            resources=resources
        )
        return [resulting_statement]
    else:
        logger.info("Exceeding policy limit, splitting statement ...")
        index = 0
        split = 0
        resulting_statements = []
        while index < len(resources):
            #  Iterating until all resources are defined in a policy statement.
            #  "index" represents the position of the resource in the resources list
            size = 0
            res = []
            while index < len(resources) and (size + len(resources[index]) + 5) < POLICY_LIMIT - POLICY_HEADERS_BUFFER - base_length:
                #  Appending a resource to the "res" list until we reach the maximum size for the resources section
                #  It compares: current size of resources versus the allowed size of the resource section in a statement
                res.append(resources[index])
                size += (len(resources[index]) + 5)  # +5 for the 4 extra characters (", ") around each resource, plus additional ones []
                index += 1
            resulting_statement = iam.PolicyStatement(
                sid=base_sid + str(split),
                effect=effect,
                actions=actions,
                resources=res
            )
            split += 1
            resulting_statements.append(resulting_statement)
        logger.info(f"Statement divided into {split+1} smaller statements")
    return resulting_statements
