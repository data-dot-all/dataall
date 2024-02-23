import { gql } from 'apollo-boost';

export const searchQueryableDatabases = ({ environmentUri, groupUri }) => ({
  variables: {
    environmentUri,
    groupUri
  },
  query: gql`
    query searchQueryableDatabases($environmentUri: String, $groupUri: String) {
      searchQueryableDatabases(
        environmentUri: $environmentUri
        groupUri: $groupUri
      ) {
        count
        nodes {
          shareUri
          itemType
          GlueDatabaseName
          GlueTableName
          principalId
          datasetUri
        }
      }
    }
  `
});
