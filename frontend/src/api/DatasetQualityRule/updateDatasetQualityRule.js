import { gql } from 'apollo-boost';

const updateDatasetQualityRule = ({ ruleUri, input }) => ({
  variables: {
    ruleUri,
    input
  },
  mutation: gql`
    mutation UpdateDatasetQualityRule(
      $ruleUri: String!
      $input: ModifyDatasetQualityRuleInput
    ) {
      updateDatasetQualityRule(ruleUri: $ruleUri, input: $input) {
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

export default updateDatasetQualityRule;
