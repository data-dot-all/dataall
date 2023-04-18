import { gql } from 'apollo-boost';

export const createDatasetQualityRule = ({ datasetUri, input }) => ({
  variables: {
    datasetUri,
    input
  },
  mutation: gql`
    mutation CreateDatasetQualityRule(
      $datasetUri: String!
      $input: NewDatasetQualityRuleInput
    ) {
      createDatasetQualityRule(datasetUri: $datasetUri, input: $input) {
        ruleUri
        name
        label
        description
        created
        query
      }
    }
  `
});
