import { gql } from 'apollo-boost';

const getSharedDatasetTables = ({ datasetUri, envUri }) => ({
  variables: {
    datasetUri,
    envUri
  },
  query: gql`
    query GetSharedDatasetTables($datasetUri: String!, $envUri: String!) {
        getSharedDatasetTables(datasetUri: $datasetUri, envUri: $envUri) {
            count
            pages
            page
            hasNext
            hasPrevious 
            nodes {
                dataset {
                  datasetUri
                }
                terms {
                  nodes {
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
  `
});

export default getSharedDatasetTables;
