import { gql } from 'apollo-boost';

const createRequest = ({ datasetUri, input }) => ({
  variables: { datasetUri, input },
  mutation: gql`
    mutation CreateShareObject(
      $datasetUri: String!
      $input: NewShareObjectInput
    ) {
      createShareObject(datasetUri: $datasetUri, input: $input) {
        shareUri
        principal {
          principalId
          principalType
        }
        created
      }
    }
  `
});

export default createRequest;
