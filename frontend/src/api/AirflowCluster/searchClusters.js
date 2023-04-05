import { gql } from 'apollo-boost';

export const searchAirflowClusters = (filter) => ({
  variables: {
    filter
  },
  query: gql`
    query searchAirflowClusters($filter: AirflowClusterFilter) {
      searchAirflowClusters(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          clusterUri
          environmentUri
          name
          label
          description
          tags
          owner
          created
          updated
          AwsAccountId
          region
          clusterArn
          clusterName
          created
          kmsAlias
          status
          CFNStackName
          CFNStackStatus
          CFNStackArn
          IAMRoleArn
          subnetIds
          securityGroupIds
          userRoleForCluster
          userRoleInEnvironment
          imported
          dagS3Path
          webServerUrl
          vpc
          organization {
            organizationUri
            label
            name
          }
          environment {
            environmentUri
            label
            name
          }
        }
      }
    }
  `
});
