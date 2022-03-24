import { gql } from 'apollo-boost';

const listOrganizations = ({ filter }) => ({
  variables: { filter },
  query: gql`
            query ListOrg($filter:OrganizationFilter){
                listOrganizations(filter:$filter){
                    count
                    nextPage
                    previousPage
                    pages
                    hasNext
                    hasPrevious
                    pageSize
                    page
                    nodes{
                        organizationUri
                        label
                        name
                        owner
                        created
                        description
                        SamlGroupName
                        tags
                        userRoleInOrganization
                        stats{
                            groups
                            users
                            environments
                        }
                    }
                }
            }
        `
});

export default listOrganizations;
