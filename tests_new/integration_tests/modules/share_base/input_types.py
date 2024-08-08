def NewShareObjectInput(environmentUri, groupUri, principalId, principalType, requestPurpose, attachMissingPolicies):
    return {
        'environmentUri': environmentUri,
        'groupUri': groupUri,
        'principalId': principalId,
        'principalType': principalType,
        'requestPurpose': requestPurpose,
        'attachMissingPolicies': attachMissingPolicies,
    }
