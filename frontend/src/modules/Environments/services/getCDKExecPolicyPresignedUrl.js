import { gql } from 'apollo-boost';

export const getCDKExecPolicyPresignedUrl = (organizationUri) => ({
  variables: {
    organizationUri
  },
  query: gql`
    query getCDKExecPolicyPresignedUrl($organizationUri: String!) {
      getCDKExecPolicyPresignedUrl(organizationUri: $organizationUri)
    }
  `
});
