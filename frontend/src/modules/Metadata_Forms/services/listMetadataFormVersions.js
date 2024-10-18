import { gql } from 'apollo-boost';

export const listMetadataFormVersions = (uri) => ({
  variables: {
    uri
  },
  query: gql`
    query listMetadataFormVersions($uri: String!) {
      listMetadataFormVersions(uri: $uri) {
        metadataFormUri
        version
        attached_forms
      }
    }
  `
});
