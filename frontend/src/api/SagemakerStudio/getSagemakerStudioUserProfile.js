import { gql } from 'apollo-boost';

export const getSagemakerStudioUserProfile = (
  sagemakerStudioUserProfileUri
) => ({
  variables: {
    sagemakerStudioUserProfileUri
  },
  query: gql`
    query getSagemakerStudioUserProfile(
      $sagemakerStudioUserProfileUri: String!
    ) {
      getSagemakerStudioUserProfile(
        sagemakerStudioUserProfileUri: $sagemakerStudioUserProfileUri
      ) {
        sagemakerStudioUserProfileUri
        name
        owner
        description
        label
        created
        tags
        userRoleForSagemakerStudioUserProfile
        sagemakerStudioUserProfileStatus
        SamlAdminGroupName
        sagemakerStudioUserProfileApps {
          DomainId
          UserProfileName
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
