import { gql } from 'apollo-boost';

const deleteApiKey = (ApiKeyId) => ({
  variables: {
    ApiKeyId
  },
  mutation: gql`
            mutation DeleteApiKey($ApiKeyId:String!){
                deleteApiKey(ApiKeyId:$ApiKeyId)
            }
        `
});

export default deleteApiKey;
