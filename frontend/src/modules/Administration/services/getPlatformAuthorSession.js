import { gql } from 'apollo-boost';

export const getPlatformAuthorSession = (awsAccount) => ({
  variables: {
    awsAccount
  },
  query: gql`
    query getPlatformAuthorSession($awsAccount: String) {
      getPlatformAuthorSession(awsAccount: $awsAccount)
    }
  `
});
