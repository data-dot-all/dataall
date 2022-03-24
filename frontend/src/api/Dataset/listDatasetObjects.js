import { gql } from 'apollo-boost';

const listDatasetObjects = ({ datasetUri, filter }) => ({
  variables: {
    datasetUri,
    filter
  },
  query: gql`
            query GetDataset($datasetUri:String!,$filter:DatasetTableFilter){
                getDataset(datasetUri:$datasetUri){
                    datasetUri
                    locations(filter:$filer){
                        count
                        page
                        pages
                        hasNext
                        hasPrevious
                        nodes{
                            locationUri
                            created
                            label
                        }
                    }

                }
                    tables(filter:$filter){
                        count
                        page
                        pages
                        hasNext
                        hasPrevious
                        nodes{
                            datasetUri
                            tableUri
                            created
                            GlueTableName
                            label
                        }
                    }

                }
            }
        `
});

export default listDatasetObjects;
