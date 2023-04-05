import { gql } from 'apollo-boost';

export const removeSharedItem = ({ shareItemUri }) => ({
  variables: {
    shareItemUri
  },
  mutation: gql`
    mutation RemoveSharedItem($shareItemUri: String!) {
      removeSharedItem(shareItemUri: $shareItemUri)
    }
  `
});
