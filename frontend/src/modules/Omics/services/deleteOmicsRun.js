import { gql } from 'apollo-boost';

// TODO: not used at the moment! Needs to be implemented
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
