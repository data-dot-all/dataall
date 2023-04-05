import { gql } from 'apollo-boost';

export const postFeedMessage = ({ targetUri, targetType, input }) => ({
  variables: {
    targetUri,
    targetType,
    input
  },
  mutation: gql`
    mutation PostFeedMessage(
      $targetUri: String!
      $targetType: String!
      $input: FeedMessageInput!
    ) {
      postFeedMessage(
        targetUri: $targetUri
        targetType: $targetType
        input: $input
      ) {
        feedMessageUri
        content
        created
        creator
      }
    }
  `
});
