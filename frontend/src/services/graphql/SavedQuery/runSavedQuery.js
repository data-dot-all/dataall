import { gql } from 'apollo-boost';

export const runSavedQuery = ({ savedQueryUri, sqlBody }) => ({
  variables: {
    savedQueryUri,
    // environmentUri: environmentUri,
    sqlBody
  },
  query: gql`
    query RunSavedQuery($savedQueryUri: String!, $sqlBody: String) {
      runSavedQuery(savedQueryUri: $savedQueryUri, sqlBody: $sqlBody) {
        metadata {
          Name
          DataType
        }
        rows {
          data
        }
      }
    }
  `
});
