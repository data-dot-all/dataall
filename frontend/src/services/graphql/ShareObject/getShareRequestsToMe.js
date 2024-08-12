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
            principalName
            principalType
            principalId
            principalRoleName
            SamlGroupName
            environmentName
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
            datasetType
            SamlAdminGroupName
            environmentName
            exists
          }
        }
      }
    }
  `
});
