import { gql } from 'apollo-boost';

export const listEnvironmentClusters = (environmentUri, filter) => ({
  variables: {
    environmentUri,
    filter
  },
  query: gql`
    query listEnvironmentClusters(
      $environmentUri: String!
      $filter: RedshiftClusterFilter
    ) {
      listEnvironmentClusters(
        environmentUri: $environmentUri
        filter: $filter
      ) {
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
          databaseName
          databaseUser
          masterUsername
          masterDatabaseName
          nodeType
          numberOfNodes
          kmsAlias
          status
          subnetGroupName
          CFNStackName
          CFNStackStatus
          CFNStackArn
          port
          endpoint
          IAMRoles
          subnetIds
          securityGroupIds
          userRoleForCluster
          userRoleInEnvironment
          imported
          stack {
            status
          }
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
