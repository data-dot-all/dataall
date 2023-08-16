import { gql } from 'apollo-boost';

<<<<<<<< HEAD:frontend/src/modules/MLStudio/services/listSagemakerStudioUsers.js
export const listSagemakerStudioUsers = (filter) => ({
========
const listSagemakerStudioUsers = (filter) => ({
>>>>>>>> modularization-main:frontend/src/api/MLStudio/listSagemakerStudioUsers.js
  variables: {
    filter
  },
  query: gql`
    query listSagemakerStudioUsers($filter: SagemakerStudioUserFilter) {
      listSagemakerStudioUsers(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          sagemakerStudioUserUri
          name
          owner
          description
          label
          created
          tags
          sagemakerStudioUserStatus
          userRoleForSagemakerStudioUser
          environment {
            label
            name
            environmentUri
            AwsAccountId
            region
            SamlGroupName
          }
          organization {
            label
            name
            organizationUri
          }
          stack {
            stack
            status
          }
        }
      }
    }
  `
});
<<<<<<<< HEAD:frontend/src/modules/MLStudio/services/listSagemakerStudioUsers.js
========

export default listSagemakerStudioUsers;
>>>>>>>> modularization-main:frontend/src/api/MLStudio/listSagemakerStudioUsers.js
