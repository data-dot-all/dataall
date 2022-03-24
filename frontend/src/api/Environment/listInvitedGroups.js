import { gql } from 'apollo-boost';

const listEnvironmentGroups = ({ filter, environmentUri }) => ({
  variables: {
    environmentUri,
    filter
  },
  query: gql`
            query listEnvironmentGroups($filter:GroupFilter,$environmentUri:String){
                listEnvironmentGroups(environmentUri:$environmentUri,filter:$filter){
                    count
                    page
                    pages
                    hasNext
                    hasPrevious
                    nodes{
                        groupUri
                        invitedBy
                        created
                        description
                    }
                }
            }
        `
});

export default listEnvironmentGroups;
