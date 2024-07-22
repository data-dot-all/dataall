import { gql } from 'apollo-boost';

export const deleteRedshiftDatasetTable = ({ rsTableUri }) => ({
  variables: {
    rsTableUri
  },
  mutation: gql`
    mutation deleteRedshiftDatasetTable($rsTableUri: String!) {
      deleteRedshiftDatasetTable(rsTableUri: $rsTableUri)
    }
  `
});
