import { gql } from 'apollo-boost';

const getShareRequestsFromMe = ({ filter }) => ({
  variables: { filter },
  query: gql`
    query getShareRequestsFromMe($filter: ShareObjectFilter) {
      getShareRequestsFromMe(filter: $filter) {
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

export default getShareRequestsFromMe;
