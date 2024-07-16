import { gql } from 'apollo-boost';

export const getRedshiftDatasetTable = (rsTableUri) => ({
  variables: {
    rsTableUri
  },
  query: gql`
    query getRedshiftDatasetTable($rsTableUri: String!) {
      getRedshiftDatasetTable(rsTableUri: $rsTableUri) {
        rsTableUri
        owner
        description
        label
        name
        region
      }
    }
  `
});
