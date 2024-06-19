import { gql } from 'apollo-boost';

export const createShareObject = ({ datasetUri, itemUri, itemType, input }) => {
  return {
    variables: {
      datasetUri,
      input,
      itemUri,
      itemType
    },
    mutation: gql`
      mutation CreateShareObject(
        $datasetUri: String!
        $itemType: String
        $itemUri: String
        $input: NewShareObjectInput!
      ) {
        createShareObject(
          datasetUri: $datasetUri
          itemType: $itemType
          itemUri: $itemUri
          input: $input
        ) {
          shareUri
          created
          alreadyExisted
        }
      }
    `
  };
};
