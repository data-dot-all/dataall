import { gql } from 'apollo-boost';

const generateEnvironmentAccessToken = ({ environmentUri }) => ({
  variables: {
    environmentUri
  },
  query: gql`
    query GenerateEnvironmentAccessToken($environmentUri: String) {
      generateEnvironmentAccessToken(environmentUri: $environmentUri)
    }
  `
});

export default generateEnvironmentAccessToken;
