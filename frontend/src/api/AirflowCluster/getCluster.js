import { gql } from 'apollo-boost';

const getCluster = (clusterUri) => ({
  variables: {
    clusterUri
  },
  query: gql`
            query GetAirflowCluster($clusterUri:String!){
                getAirflowCluster(clusterUri:$clusterUri){
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
                     maxWorkers
                     environmentClass
                     kmsAlias
                     status
                     CFNStackName
                     CFNStackStatus
                     CFNStackArn
                     IAMRoleArn
                     subnetIds
                     vpc
                     securityGroupIds
                     userRoleForCluster
                     userRoleInEnvironment
                     imported
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
                     stack{
                        stack
                        status
                        stackUri
                        targetUri
                        accountid
                        region
                        stackid
                        link
                        outputs
                        resources
                    }
                }
            }
        `
});

export default getCluster;
