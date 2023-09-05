import { gql } from 'apollo-boost';

export const listFeedMessages = ({ targetUri, targetType, filter }) => ({
  variables: {
    targetUri,
    targetType,
    filter
  },
  query: gql`
    query GetFeed(
      $targetUri: String!
      $targetType: String!
      $filter: FeedMessageFilter
    ) {
      getFeed(targetUri: $targetUri, targetType: $targetType) {
        messages(filter: $filter) {
          count
          hasNext
          hasPrevious
          page
          pages
          nodes {
            content
            feedMessageUri
            creator
            created
          }
        }
      }
    }
  `
});
