import { gql } from 'apollo-boost';

const getCDKExecPolicyPresignedUrl = (organizationUri) => ({
  variables: {
    organizationUri
  },
  query: gql`
    query getCDKExecPolicyPresignedUrl($organizationUri: String!) {
      getCDKExecPolicyPresignedUrl(organizationUri: $organizationUri)
    }
  `
});

export default getCDKExecPolicyPresignedUrl;
