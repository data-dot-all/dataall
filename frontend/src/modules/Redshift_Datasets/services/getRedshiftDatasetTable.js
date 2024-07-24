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
        dataset {
          owner
          SamlAdminGroupName
          datasetUri
          name
          label
          userRoleForDataset
          organization {
            label
          }
          environment {
            label
          }
          region
        }
      }
    }
  `
});
