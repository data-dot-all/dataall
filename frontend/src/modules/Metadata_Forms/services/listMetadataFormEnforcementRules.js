import { gql } from 'apollo-boost';

export const listMetadataFormEnforcementRules = (uri) => ({
  variables: {
    uri
  },
  query: gql`
    query listMetadataFormEnforcementRules($uri: String!) {
      listMetadataFormEnforcementRules(uri: $uri) {
        uri
        level
        homeEntity
        homeEntityName
        entityTypes
        metadataFormUri
        version
      }
    }
  `
});
