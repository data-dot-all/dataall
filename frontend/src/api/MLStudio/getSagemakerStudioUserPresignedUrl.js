import { gql } from 'apollo-boost';

const getSagemakerStudioUserPresignedUrl = (
  sagemakerStudioUserUri
) => ({
  variables: {
    sagemakerStudioUserUri
  },
  query: gql`
    query getSagemakerStudioUserPresignedUrl(
      $sagemakerStudioUserUri: String!
    ) {
      getSagemakerStudioUserPresignedUrl(
        sagemakerStudioUserUri: $sagemakerStudioUserUri
      )
    }
  `
});

export default getSagemakerStudioUserPresignedUrl;
