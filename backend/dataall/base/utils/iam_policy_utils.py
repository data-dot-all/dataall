from typing import List

POLICY_LIMIT = 6144

def split_policy_statements_in_chunks(statements: List):
    """
    Splits a list of IAM policy statements into a list of lists (chunks)
    For each chunk, the size should remain below the POLICY LIMIT
    """
    chunks = []
    index = 0
    print("Initial loop")
    # Index = number of statements
    print(f"statements = {len(statements)}")
    while index < len(statements):
        chunk = []
        chunk_size = len(statements[index].to_string())
        print(f"-----------------")
        print(f"chunk = {chunk}")
        print(f"chunk_size = {chunk_size}")
        while chunk_size + len(statements[index].to_string()) < POLICY_LIMIT:
            for statement in statements[index:]:
                print(statement.to_string())
                chunk.append(statement)
                print(f"statement size= {len(statement.to_string())}")
                chunk_size += len(statement.to_string())
                index += 1
                print(f"################")
                #print(f"chunk = {chunk}")
                print(f"chunk_size = {chunk_size}")
                print(f"index={index}")
        chunks.append(chunk)
        print(chunks)

    return chunks


def split_policy_with_resources_in_statements(statement_without_resources, resources):
    """
    Ensures that the size of an IAM statement is below the POLICY LIMIT
    If it exceeds the POLICY LIMIT, it breaks the statement in multiple statements
    """
    resulting_statement = statement_without_resources.replace("RESOURCES", resources)
    if len(str(resulting_statement)) < POLICY_LIMIT:
        return [resulting_statement]
    else:
        resulting_statements = []
        splits = len(str(resources))/(POLICY_LIMIT-len(str(statement_without_resources)))
        print(splits)
        split_size = len(str(resulting_statement))/splits
        for index in range(splits):
            print(index)
            print(index+split_size)
            resulting_statement = statement_without_resources.replace("RESOURCES", resources[index,index+split_size])
            resulting_statements.append((resulting_statement))
    return resulting_statements


