import { gql } from 'apollo-boost';

<<<<<<<< HEAD:frontend/src/modules/MLStudio/services/getSagemakerStudioUser.js
export const getSagemakerStudioUser = (sagemakerStudioUserUri) => ({
========
const getSagemakerStudioUser = (sagemakerStudioUserUri) => ({
>>>>>>>> modularization-main:frontend/src/api/MLStudio/getSagemakerStudioUser.js
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
<<<<<<<< HEAD:frontend/src/modules/MLStudio/services/getSagemakerStudioUser.js
========

export default getSagemakerStudioUser;
>>>>>>>> modularization-main:frontend/src/api/MLStudio/getSagemakerStudioUser.js
