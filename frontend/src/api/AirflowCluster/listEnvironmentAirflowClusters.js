import { gql } from 'apollo-boost';

const listEnvironmentAirflowClusters = (environmentUri, filter) => ({
  variables: {
    environmentUri,
    filter
  },
  query: gql`
            query listEnvironmentAirflowClusters($environmentUri:String!, $filter:AirflowClusterFilter){
                listEnvironmentAirflowClusters(environmentUri:$environmentUri,filter:$filter){
                    count
                    page
                    pages
                    hasNext
                    hasPrevious
                    nodes{
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
                     stack{
                       status
                     }
                     vpc
                        organization{
                            organizationUri
                            label
                            name
                        }
                        environment{
                            environmentUri
                            label
                            name
                        }

                    }
                }
            }
        `
});

export default listEnvironmentAirflowClusters;
