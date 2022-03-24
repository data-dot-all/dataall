import { gql } from 'apollo-boost';

const listTenantPermissions = (filter) => ({
  variables: {
    filter
  },
  query: gql`
            query listTenantPermissions{
            listTenantPermissions{
                name
                description
            }
        }
        `
});

export default listTenantPermissions;
