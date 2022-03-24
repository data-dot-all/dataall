import { gql } from 'apollo-boost';

const listDatasetTableProfilingJobs = (tableUri) => ({
  variables: {
    tableUri
  },
  query: gql`
            query GetDatasetTable($tableUri:String!){
                getDatasetTable(tableUri:$tableUri){
                        datasetUri
                        owner
                        created
                        tableUri
                        AwsAccountId
                        GlueTableName
                        profilingJobs{
                            count
                            page
                            pages
                            hasNext
                            hasPrevious
                            nodes{
                                jobUri
                                created
                                status
                            }

                        }
                    }
                }
        `
});

export default listDatasetTableProfilingJobs;
