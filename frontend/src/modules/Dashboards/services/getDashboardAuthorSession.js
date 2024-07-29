import { gql } from 'apollo-boost';

export const getAuthorSession = (environmentUri) => ({
  variables: {
    environmentUri
  },
  query: gql`
    query GetAuthorSession($environmentUri: String!) {
      getAuthorSession(environmentUri: $environmentUri)
    }
  `
});
