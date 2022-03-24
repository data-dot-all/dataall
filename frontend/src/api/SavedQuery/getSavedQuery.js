import { gql } from 'apollo-boost';

const getSavedQuery = (queryUri) => ({
  variables: {
    queryUri
  },
  query: gql`
            query getSavedQuery ($queryUri:String!){
                getSavedQuery (queryUri:$queryUri){
                    savedQueryUri
                    name
                    label
                    description
                    owner
                    description
                    sqlBody
                    label
                    created
                    tags
                }
            }
        `
});

export default getSavedQuery;
