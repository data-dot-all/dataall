import { gql } from 'apollo-boost';

const getPivotRoleName = (organizationUri) => ({
  variables: {
    organizationUri
  },
  query: gql`
    query getPivotRoleName($organizationUri: String!) {
      getPivotRoleName(organizationUri: $organizationUri)
    }
  `
});

export default getPivotRoleName;
