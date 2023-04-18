import { gql } from 'apollo-boost';

export const deleteAirflowProject = ({ projectUri }) => ({
  variables: { projectUri },
  mutation: gql`
    mutation deleteAirflowProject($projectUri: String) {
      deleteAirflowProject(projectUri: $projectUri)
    }
  `
});
