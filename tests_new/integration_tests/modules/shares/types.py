Principal = """
          principalName
          principalType
          principalId
          principalRoleName
          SamlGroupName
          environmentName
"""

Dataset = """
datasetUri
datasetName
SamlAdminGroupName
environmentName
AwsAccountId
region
exists
description
"""


ShareItem = """
shareUri,
shareItemUri,
itemUri,
status,
action,
itemType,
itemName,
description,
healthStatus,
healthMessage,
lastVerificationTime,
"""


SharedItemSearchResult = f"""
count,
pageSize,
nextPage,
pages,
page,
previousPage,
hasNext,
hasPrevious,
nodes {{
    {ShareItem}
}}
"""

ShareObject = f"""
shareUri,
status,
owner,
created,
deleted,
updated,
datasetUri,
requestPurpose,
rejectPurpose,
dataset {{
    {Dataset}
}},
alreadyExisted,
existingSharedItems,
principal {{
    {Principal}
}},
items(filter: $filter){{
    {SharedItemSearchResult}
}},
canViewLogs,
userRoleForShareObject,
"""
