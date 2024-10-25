import { gql } from 'apollo-boost';

export const getRedshiftDatasetTable = ({ rsTableUri }) => ({
  variables: {
    rsTableUri
  },
  query: gql`
    query getRedshiftDatasetTable($rsTableUri: String!) {
      getRedshiftDatasetTable(rsTableUri: $rsTableUri) {
        rsTableUri
        name
        label
        created
        description
        tags
        terms {
          count
          nodes {
            __typename
            ... on Term {
              nodeUri
              path
              label
            }
          }
        }
        dataset {
          owner
          SamlAdminGroupName
          datasetUri
          name
          label
          userRoleForDataset
          environment {
            environmentUri
            label
            region
            organization {
              organizationUri
              label
            }
          }
          region
        }
      }
    }
  `
});
