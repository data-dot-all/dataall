import { gql } from 'apollo-boost';

const listDatasetShareObjects = ({ datasetUri, filter }) => ({
  variables: {
    datasetUri,
    filter
  },
  query: gql`query ListDatasetShareObjects($datasetUri:String!,$filter:ShareObjectFilter){
            getDataset(datasetUri:$datasetUri){
                shares(filter:$filter){
                    page
                    pages
                    pageSize
                    hasPrevious
                    hasNext
                    count
                    nodes{
                        owner
                        created
                        deleted
                        shareUri
                        status
                        userRoleForShareObject
                        principal{
                            principalId
                            principalType
                            principalName
                            AwsAccountId
                            region
                        }
                        statistics{
                            tables
                            locations
                        }
                        dataset{
                            datasetUri
                            datasetName
                            datasetOrganizationName
                            datasetOrganizationUri
                        }
                    }

                }
            }
        }`
});

export default listDatasetShareObjects;
