import { gql } from 'apollo-boost';

export const removeSavedQuery = (queryUri) => ({
  variables: {
    queryUri
  },
  mutation: gql`
    mutation RemoveSavedQuery($queryUri: String!) {
      removeSavedQuery(savedQueryUri: $queryUri)
    }
  `
});
