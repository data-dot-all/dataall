import { gql } from 'apollo-boost';

const revokeSharedItem = ({ shareItemUri }) => ({
  variables: {
    shareItemUri
  },
  mutation: gql`
    mutation revokeSharedItem($shareItemUri: String!) {
      revokeSharedItem(shareItemUri: $shareItemUri)
    }
  `
});

export default revokeSharedItem;
