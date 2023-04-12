import { gql } from 'apollo-boost';

export const createApiKey = () => ({
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
