import { gql } from 'apollo-boost';

export const getDatasetQualityRule = (ruleUri) => ({
  variables: {
    ruleUri
  },
  query: gql`
    query GetDatasetQualityRule($ruleUri: String!) {
      getDatasetQualityRule(ruleUri: $ruleUri) {
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
