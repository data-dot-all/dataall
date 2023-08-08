import { gql } from 'apollo-boost';

export const getSagemakerStudioUser = (sagemakerStudioUserUri) => ({
  variables: {
    sagemakerStudioUserUri
  },
  query: gql`
    query getSagemakerStudioUser($sagemakerStudioUserUri: String!) {
      getSagemakerStudioUser(sagemakerStudioUserUri: $sagemakerStudioUserUri) {
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
        sagemakerStudioUserApps {
          DomainId
          UserName
          AppType
          AppName
          Status
        }
        environment {
          label
          name
          environmentUri
          AwsAccountId
          region
          EnvironmentDefaultIAMRoleArn
        }
        organization {
          label
          name
          organizationUri
        }
        stack {
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
        }
      }
    }
  `
});
