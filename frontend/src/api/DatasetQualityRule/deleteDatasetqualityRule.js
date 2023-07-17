import { gql } from 'apollo-boost';

const deleteDatasetQualityRule = (ruleUri) => ({
  variables: {
    ruleUri
  },
  mutation: gql`
    mutation DeleteDatasetQualityRule($ruleUri: String!) {
      deleteDatasetQualityRule(ruleUri: $ruleUri)
    }
  `
});

export default deleteDatasetQualityRule;
