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
nodes {
ShareItem
}
""",

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
dataset,
alreadyExisted,
existingSharedItems,
statistics,
principal,
environment,
group,
items(filter: ShareableObjectFilter): {
    SharedItemSearchResult
},
canViewLogs,
userRoleForShareObject,
"""


