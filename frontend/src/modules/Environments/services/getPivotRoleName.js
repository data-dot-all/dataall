import { gql } from 'apollo-boost';

export const getPivotRoleName = (organizationUri) => ({
  variables: {
    organizationUri
  },
  query: gql`
    query getPivotRoleName($organizationUri: String!) {
      getPivotRoleName(organizationUri: $organizationUri)
    }
  `
});
