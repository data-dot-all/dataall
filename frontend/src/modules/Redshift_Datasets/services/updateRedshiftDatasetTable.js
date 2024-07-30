import { gql } from 'apollo-boost';

export const updateRedshiftDatasetTable = ({ rsTableUri, input }) => ({
  variables: {
    rsTableUri,
    input
  },
  mutation: gql`
    mutation updateRedshiftDatasetTable(
      $rsTableUri: String!
      $input: ModifyRedshiftDatasetInput
    ) {
      updateRedshiftDatasetTable(rsTableUri: $rsTableUri, input: $input) {
        rsTableUri
        label
      }
    }
  `
});
