import { gql } from 'apollo-boost';

const listOrganizationNotInvitedGroups = ({ filter, organizationUri }) => ({
  variables: {
    organizationUri,
    filter
  },
  query: gql`
            query listOrganizationNotInvitedGroups($filter:GroupFilter,$organizationUri:String){
                listOrganizationNotInvitedGroups(organizationUri:$organizationUri,filter:$filter){
                    count
                    page
                    pages
                    hasNext
                    hasPrevious
                    nodes{
                        groupUri
                    }
                }
            }
        `
});

export default listOrganizationNotInvitedGroups;
