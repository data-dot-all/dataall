import { gql } from 'apollo-boost';

const createApiKey = () => ({
  mutation: gql`
    mutation CreateApiKey {
      createApiKey {
        ApiKeyId
        ApiKeySecret
        expires
      }
    }
  `
});

export default createApiKey;
