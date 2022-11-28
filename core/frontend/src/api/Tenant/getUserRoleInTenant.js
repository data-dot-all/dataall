import { gql } from 'apollo-boost';

const getUserRoleInTenant = () => ({
  query: gql`
    query GetUserRoleInTenant {
      getUserRoleInTenant
    }
  `
});

export default getUserRoleInTenant;
