import { gql } from 'apollo-boost';

const generateEnvironmentAccessToken = ({ environmentUri, groupUri }) => ({
  variables: {
    environmentUri,
    groupUri
  },
  query: gql`
    query GenerateEnvironmentAccessToken(
      $environmentUri: String!
      $groupUri: String
    ) {
      generateEnvironmentAccessToken(
        environmentUri: $environmentUri
        groupUri: $groupUri
      )
    }
  `
});

export default generateEnvironmentAccessToken;
