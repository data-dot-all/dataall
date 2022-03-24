import { gql } from 'apollo-boost';

const listTenantGroups = (filter) => ({
  variables: {
    filter
  },
  query: gql`
            query listTenantGroups($filter:GroupFilter){
                listTenantGroups(filter:$filter){
                    count
                    page
                    pages
                    hasNext
                    hasPrevious
                    nodes{
                        groupUri
                        tenantPermissions{
                            name
                            description
                        }
                    }
                }
            }
        `
});

export default listTenantGroups;
