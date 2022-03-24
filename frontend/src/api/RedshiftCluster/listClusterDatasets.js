import { gql } from 'apollo-boost';

const listClusterDatasets = ({ clusterUri, filter }) => ({
  variables: {
    clusterUri,
    filter
  },
  query: gql`
            query ListRedshiftClusterDatasets($clusterUri:String!,$filter:RedshiftClusterDatasetFilter){
                listRedshiftClusterDatasets(clusterUri:$clusterUri,filter:$filter){
                    count
                    page
                    pages
                    hasNext
                    hasPrevious
                    nodes{
                        datasetUri
                        name
                        AwsAccountId
                        region
                        S3BucketName
                        GlueDatabaseName
                        created
                        owner
                        label
                        region
                        tags
                        userRoleForDataset
                        redshiftClusterPermission(clusterUri:$clusterUri)
                        redshiftDataCopyEnabled(clusterUri:$clusterUri)
                        description
                        organization{
                            name
                            organizationUri
                            label
                        }
                        statistics{
                            tables
                            locations
                        }
                        environment{
                            environmentUri
                            name
                            AwsAccountId
                            SamlGroupName
                            region
                        }

                    }
                }
            }
        `
});

export default listClusterDatasets;
