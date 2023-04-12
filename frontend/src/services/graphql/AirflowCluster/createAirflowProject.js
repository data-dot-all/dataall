import { gql } from 'apollo-boost';

export const createAirflowProject = ({ clusterUri, input }) => ({
  variables: {
    clusterUri,
    projectInput: input
  },
  mutation: gql`
    mutation createAirflowClusterProject(
      $clusterUri: String!
      $projectInput: NewAirflowProjectInput!
    ) {
      createAirflowClusterProject(
        clusterUri: $clusterUri
        projectInput: $projectInput
      ) {
        projectUri
        name
        label
        created
      }
    }
  `
});
