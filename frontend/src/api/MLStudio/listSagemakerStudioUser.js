import { gql } from 'apollo-boost';

const listSagemakerStudioUsers = (filter) => ({
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

export default listSagemakerStudioUsers;
