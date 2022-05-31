import { gql } from 'apollo-boost';

const getPivotRolePresignedUrl = (organizationUri) => ({
  variables: {
    organizationUri
  },
  query: gql`
    query getPivotRolePresignedUrl($organizationUri: String!) {
      getPivotRolePresignedUrl(organizationUri: $organizationUri)
    }
  `
});

export default getPivotRolePresignedUrl;
