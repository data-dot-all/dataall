def get_smstudio_user(client, uri):
    query = {
        'operationName': 'getSagemakerStudioUser',
        'variables': {
            'sagemakerStudioUserUri': uri,
        },
        'query': f"""
                    query getSagemakerStudioUser($sagemakerStudioUserUri: String!) {{
                        getSagemakerStudioUser(sagemakerStudioUserUri: $sagemakerStudioUserUri) {{
                            sagemakerStudioUserUri
                            name
                            owner
                            description
                            label
                            created
                            tags
                            userRoleForSagemakerStudioUser
                            sagemakerStudioUserStatus
                            SamlAdminGroupName
                            sagemakerStudioUserApps {{
                                DomainId
                                UserName
                                AppType
                                AppName
                                Status
                            }}
                            environment {{
                                label
                                name
                                environmentUri
                                AwsAccountId
                                region
                                EnvironmentDefaultIAMRoleArn
                            }}
                            organization {{
                                label
                                name
                                organizationUri
                            }}
                            stack {{
                                stack
                                status
                                stackUri
                                targetUri
                                accountid
                                region
                                stackid
                                link
                                outputs
                                resources
                            }}
                        }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.getSagemakerStudioUser


def list_smstudio_users(client, term=None):
    query = {
        'operationName': 'listSagemakerStudioUsers',
        'variables': {
            'filter': {'term': term},
        },
        'query': f"""
                    query listSagemakerStudioUsers($filter: SagemakerStudioUserFilter) {{
                      listSagemakerStudioUsers(filter: $filter) {{
                        count
                        page
                        pages
                        hasNext
                        hasPrevious
                        nodes {{
                          sagemakerStudioUserUri
                          name
                          owner
                          description
                          label
                          created
                          tags
                          sagemakerStudioUserStatus
                          userRoleForSagemakerStudioUser
                          environment {{
                            label
                            name
                            environmentUri
                            AwsAccountId
                            region
                            SamlGroupName
                          }}
                          organization {{
                            label
                            name
                            organizationUri
                          }}
                          stack {{
                            stack
                            status
                          }}
                        }}
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.listSagemakerStudioUsers


def get_smstudio_user_presigned_url(client, uri):
    query = {
        'operationName': 'getSagemakerStudioUserPresignedUrl',
        'variables': {
            'sagemakerStudioUserUri': uri,
        },
        'query': f"""
                    query getSagemakerStudioUserPresignedUrl($sagemakerStudioUserUri: String!) {{
                      getSagemakerStudioUserPresignedUrl(
                        sagemakerStudioUserUri: $sagemakerStudioUserUri
                      )
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.getSagemakerStudioUserPresignedUrl


def get_environment_mlstudio_domain(client, uri):
    query = {
        'operationName': 'getEnvironmentMLStudioDomain',
        'variables': {
            'environmentUri': uri,
        },
        'query': f"""
                    query getEnvironmentMLStudioDomain($environmentUri: String!) {{
                      getEnvironmentMLStudioDomain(environmentUri: $environmentUri) {{
                        sagemakerStudioUri
                        environmentUri
                        label
                        sagemakerStudioDomainName
                        DefaultDomainRoleName
                        vpcType
                        vpcId
                        subnetIds
                        owner
                        created
                      }}
                    }}
                """,
    }
    response = client.query(query=query)
    return response.data.getEnvironmentMLStudioDomain
