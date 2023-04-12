import { gql } from 'apollo-boost';

export const deleteDatasetQualityRule = (ruleUri) => ({
  variables: {
    ruleUri
  },
  mutation: gql`
    mutation DeleteDatasetQualityRule($ruleUri: String!) {
      deleteDatasetQualityRule(ruleUri: $ruleUri)
    }
  `
});
