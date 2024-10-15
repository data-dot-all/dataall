def NewShareObjectInput(
    environmentUri, groupUri, principalId, principalType, requestPurpose, attachMissingPolicies, permissions
):
    return {
        'environmentUri': environmentUri,
        'groupUri': groupUri,
        'principalId': principalId,
        'principalType': principalType,
        'requestPurpose': requestPurpose,
        'attachMissingPolicies': attachMissingPolicies,
        'permissions': permissions,
    }
