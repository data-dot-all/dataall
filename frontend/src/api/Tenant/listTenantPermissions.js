import { gql } from 'apollo-boost';

export const listTenantPermissions = (filter) => ({
  variables: {
    filter
  },
  query: gql`
    query listTenantPermissions {
      listTenantPermissions {
        name
        description
      }
    }
  `
});
