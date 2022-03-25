import { gql } from 'apollo-boost';

const searchOutbox = ({ filter }) => ({
  variables: { filter },
  query: gql`
    query RequestsFromMe($filter: ShareObjectFilter) {
      requestsFromMe(filter: $filter) {
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
            AwsAccountId
            region
          }
          statistics {
            tables
            locations
          }
          dataset {
            datasetUri
            datasetName
            datasetOrganizationName
            datasetOrganizationUri
          }
        }
      }
    }
  `
});

export default searchOutbox;
