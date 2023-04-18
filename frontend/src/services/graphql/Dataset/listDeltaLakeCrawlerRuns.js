import { gql } from 'apollo-boost';

export const listDeltaLakeCrawlerRuns = ({ datasetUri }) => ({
  variables: {
    datasetUri
  },
  query: gql`
    query listDeltaLakeCrawlerRuns($datasetUri: String!) {
      listDeltaLakeCrawlerRuns(datasetUri: $datasetUri) {
        datasetUri
        GlueJobName
        GlueJobRunId
        AwsAccountId
        GlueTriggerName
        created
        status
        owner
      }
    }
  `
});
