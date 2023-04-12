import { gql } from 'apollo-boost';

export const deleteApiKey = (ApiKeyId) => ({
  variables: {
    ApiKeyId
  },
  mutation: gql`
    mutation DeleteApiKey($ApiKeyId: String!) {
      deleteApiKey(ApiKeyId: $ApiKeyId)
    }
  `
});
