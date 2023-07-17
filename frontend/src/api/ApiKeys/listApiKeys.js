import { gql } from 'apollo-boost';

const listApiKeys = () => ({
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

export default listApiKeys;
