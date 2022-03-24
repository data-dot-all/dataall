import { gql } from 'apollo-boost';

const listDatasetTables = ({ datasetUri, filter }) => ({
  variables: {
    datasetUri,
    filter
  },
  query: gql`
            query GetDataset($datasetUri:String!,$filter:DatasetTableFilter){
                getDataset(datasetUri:$datasetUri){
                    tables(filter:$filter){
                        count
                        page
                        pages
                        hasNext
                        hasPrevious
                        nodes{
                            dataset{
                                datasetUri
                            }
                            terms{
                                nodes{
                                    label
                                }
                            }
                            tableUri
                            name
                            created
                            GlueTableName
                            GlueDatabaseName
                            description
                            stage
                            S3Prefix
                            userRoleForTable
                        }
                    }

                }
            }
        `
});

export default listDatasetTables;
