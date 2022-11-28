import { gql } from 'apollo-boost';

const createAirflowCluster = ({ environmentUri, input }) => ({
  variables: {
    environmentUri,
    clusterInput: input
  },
  mutation: gql`
    mutation createAirflowCluster(
      $environmentUri: String!
      $clusterInput: NewAirflowClusterInput!
    ) {
      createAirflowCluster(
        environmentUri: $environmentUri
        clusterInput: $clusterInput
      ) {
        clusterUri
        name
        label
        created
      }
    }
  `
});

export default createAirflowCluster;
