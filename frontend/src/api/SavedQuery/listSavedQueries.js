import { gql } from 'apollo-boost';

const listSavedQueries = (filter) => ({
  variables: {
    filter
  },
  query: gql`
            query ListSavedQueries($filter:SavedQueryFilter){
                listSavedQueries(filter:$filter){
                    count
                    page
                    pages
                    hasNext
                    hasPrevious
                    nodes{
                        savedQueryUri
                        name
                        owner
                        description
                        label
                        created
                        tags
                    }
                }
            }
        `
});

export default listSavedQueries;
