import { gql } from 'apollo-boost';

const removeSavedQuery = (queryUri) => ({
  variables: {
    queryUri
  },
  mutation: gql`
    mutation RemoveSavedQuery($queryUri: String!) {
      removeSavedQuery(savedQueryUri: $queryUri)
    }
  `
});

export default removeSavedQuery;
