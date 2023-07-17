import { gql } from 'apollo-boost';

const getPlatformAuthorSession = (awsAccount) => ({
  variables: {
    awsAccount
  },
  query: gql`
    query getPlatformAuthorSession($awsAccount: String) {
      getPlatformAuthorSession(
         awsAccount: $awsAccount
      )
    }
  `
});

export default getPlatformAuthorSession;
