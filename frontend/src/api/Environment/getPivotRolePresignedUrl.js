import { gql } from 'apollo-boost';

export const getPivotRolePresignedUrl = (organizationUri) => ({
  variables: {
    organizationUri
  },
  query: gql`
    query getPivotRolePresignedUrl($organizationUri: String!) {
      getPivotRolePresignedUrl(organizationUri: $organizationUri)
    }
  `
});
