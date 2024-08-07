import { gql } from 'apollo-boost';

export const getShareRequestsToMe = ({ filter }) => ({
  variables: { filter },
  query: gql`
    query getShareRequestsToMe($filter: ShareObjectFilter) {
      getShareRequestsToMe(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          owner
          created
          deleted
          shareUri
          status
          userRoleForShareObject
          principal {
            principalId
            principalType
            principalName
            principalRoleName
            SamlGroupName
            environmentUri
            environmentName
            AwsAccountId
            region
            organizationUri
            organizationName
          }
          statistics {
            sharedItems
            revokedItems
            failedItems
            pendingItems
          }
          dataset {
            datasetUri
            datasetName
            SamlAdminGroupName
            environmentName
            exists
          }
        }
      }
    }
  `
});
