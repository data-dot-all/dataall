import { gql } from 'apollo-boost';

const createDatasetQualityRule = ({ datasetUri, input }) => ({
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

export default createDatasetQualityRule;
