import { gql } from 'apollo-boost';

export const listAirflowProjects = ({ clusterUri, filter }) => ({
  variables: {
    clusterUri,
    filter
  },
  query: gql`
    query listAirflowClusterProjects(
      $clusterUri: String!
      $filter: AirflowProjectFilter
    ) {
      listAirflowClusterProjects(clusterUri: $clusterUri, filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          projectUri
          name
          packageName
          codeRepositoryName
          codeRepositoryLink
          codeRepositoryStatus
          codePipelineName
          codePipelineArn
          codePipelineLink
          description
          created
        }
      }
    }
  `
});
