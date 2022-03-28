import { gql } from 'apollo-boost';

const listDatasets = ({ filter }) => ({
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

export default listDatasets;
