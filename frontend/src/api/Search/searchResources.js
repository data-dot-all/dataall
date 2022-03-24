import { gql } from 'apollo-boost';

const SearchResources = (filter) => ({
  variables: {
    filter
  },
  query: gql`query SearchResources(
            $filter:SearchInputFilter,
        ){
            searchResources(filter:$filter){
               count
                page
                pages
                hasNext
                hasPrevious
                nodes{
                    objectUri
                    objectType
                    label
                    description
                    tags
                }
            }
        }`
});

export default SearchResources;
