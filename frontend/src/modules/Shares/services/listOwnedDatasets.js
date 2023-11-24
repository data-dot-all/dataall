import { gql } from 'apollo-boost';

export const listOwnedDatasets = ({ filter }) => ({
  variables: {
    filter
  },
  query: gql`
    query listOwnedDatasets($filter: DatasetFilter) {
      listOwnedDatasets(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          datasetUri
          owner
          description
          region
          label
          created
          SamlAdminGroupName
          userRoleForDataset
          userRoleInEnvironment
          GlueDatabaseName
          tags
          topics
          organization {
            organizationUri
            label
          }
          AwsAccountId
          environment {
            label
            AwsAccountId
            region
          }
          stack {
            status
          }
          statistics {
            tables
            locations
            upvotes
          }
        }
      }
    }
  `
});
