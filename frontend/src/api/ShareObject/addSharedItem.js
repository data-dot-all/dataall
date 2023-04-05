import { gql } from 'apollo-boost';

const addSharedItem = ({ shareUri, input }) => {
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

export default addSharedItem;
