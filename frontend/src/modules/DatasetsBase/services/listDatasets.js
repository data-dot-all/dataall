import { gql } from 'apollo-boost';

export const listDatasets = ({ filter }) => ({
  variables: {
    filter
  },
  query: gql`
    query ListDatasets($filter: DatasetFilter) {
      listDatasets(filter: $filter) {
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
          tags
          topics
          AwsAccountId
          environment {
            label
            region
            organization {
              organizationUri
              label
            }
          }
          stack {
            status
          }
          datasetType
        }
      }
    }
  `
});
