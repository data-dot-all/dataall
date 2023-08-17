import { gql } from 'apollo-boost';

export const getPivotRoleExternalId = (organizationUri) => ({
  variables: {
    organizationUri
  },
  query: gql`
    query getPivotRoleExternalId($organizationUri: String!) {
      getPivotRoleExternalId(organizationUri: $organizationUri)
    }
  `
});
