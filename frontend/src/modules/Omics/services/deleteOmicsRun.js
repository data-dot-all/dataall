import { gql } from 'apollo-boost';

export const deleteOmicsRun = (runUri, deleteFromAWS) => ({
  variables: {
    runUri,
    deleteFromAWS
  },
  mutation: gql`
    mutation deleteOmicsRun($runUri: String!, $deleteFromAWS: Boolean) {
      deleteOmicsRun(runUri: $runUri, deleteFromAWS: $deleteFromAWS)
    }
  `
});
