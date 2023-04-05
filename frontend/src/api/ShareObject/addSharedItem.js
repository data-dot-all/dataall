import { gql } from 'apollo-boost';

export const addSharedItem = ({ shareUri, input }) => {
  return {
    variables: {
      shareUri,
      input
    },
    mutation: gql`
      mutation AddSharedItem($shareUri: String!, $input: AddSharedItemInput!) {
        addSharedItem(shareUri: $shareUri, input: $input) {
          shareItemUri
        }
      }
    `
  };
};
