import { gql } from 'apollo-boost';

const deleteOmicsRun = (runUri, deleteFromAWS) => ({
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

export default deleteOmicsRun;
