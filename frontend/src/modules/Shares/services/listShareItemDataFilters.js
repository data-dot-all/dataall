import { gql } from 'apollo-boost';

export const listShareItemDataFilters = ({ shareItemUri }) => ({
  variables: {
    shareItemUri
  },
  query: gql`
    query listShareItemDataFilters($shareItemUri: String!) {
      listShareItemDataFilters(shareItemUri: $shareItemUri)
    }
  `
});
