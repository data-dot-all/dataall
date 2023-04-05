import { gql } from 'apollo-boost';

export const listApiKeys = () => ({
  query: gql`
    query ListApiKeys {
      listApiKeys {
        count
        nodes {
          ApiKeyId
          expires
        }
      }
    }
  `
});
