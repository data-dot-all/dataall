import { gql } from 'apollo-boost';

const getShareRequestsToMe = ({ filter }) => ({
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
            principalIAMRoleName
            SamlGroupName
            environmentUri
            environmentName
            AwsAccountId
            region
            organizationUri
            organizationName
          }
          statistics {
            tables
            locations
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

export default getShareRequestsToMe;
