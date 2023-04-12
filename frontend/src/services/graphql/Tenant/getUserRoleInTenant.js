import { gql } from 'apollo-boost';

export const getUserRoleInTenant = () => ({
  query: gql`
    query GetUserRoleInTenant {
      getUserRoleInTenant
    }
  `
});
