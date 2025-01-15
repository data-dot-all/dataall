import { gql } from 'apollo-boost';

export const getTrustAccount = (organizationUri) => ({
  variables: {
    organizationUri
  },
  query: gql`
    query GetTrustAccount($organizationUri: String!) {
      getTrustAccount(organizationUri: $organizationUri)
    }
  `
});
