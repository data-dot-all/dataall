import { gql } from 'apollo-boost';
export const deleteOmicsRun = (runUris, deleteFromAWS) => ({
  variables: {
    runUris,
    deleteFromAWS
  },
  mutation: gql`
    mutation deleteOmicsRun($runUris: [String!], $deleteFromAWS: Boolean) {
      deleteOmicsRun(runUris: $runUris, deleteFromAWS: $deleteFromAWS)
    }
  `
});
