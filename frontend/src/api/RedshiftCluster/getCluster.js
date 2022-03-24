import { gql } from 'apollo-boost';

const getCluster = (clusterUri) => ({
  variables: {
    clusterUri
  },
  query: gql`
            query GetRedshiftCluster($clusterUri:String!){
                getRedshiftCluster(clusterUri:$clusterUri){
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
                     datahubSecret
                     masterUsername
                     masterSecret
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
                     vpc
                     securityGroupIds
                     userRoleForCluster
                     userRoleInEnvironment
                     imported
                     SamlGroupName
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
