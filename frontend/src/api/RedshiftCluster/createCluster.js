import { gql } from 'apollo-boost';

const createRedshiftCluster = ({ environmentUri, input }) => ({
  variables: {
    environmentUri,
    clusterInput: input
  },
  mutation: gql`
    mutation createRedshiftCluster(
      $environmentUri: String!
      $clusterInput: NewClusterInput!
    ) {
      createRedshiftCluster(
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

export default createRedshiftCluster;
