import { gql } from 'apollo-boost';

export const getMetadataForm = (uri, version = null) => ({
  variables: {
    uri: uri,
    version: version
  },
  query: gql`
    query getMetadataForm($uri: String!, $version: Int) {
      getMetadataForm(uri: $uri) {
        uri
        name
        description
        SamlGroupName
        visibility
        homeEntity
        homeEntityName
        userRole
        versions
        fields(version: $version) {
          uri
          metadataFormUri
          name
          displayNumber
          description
          required
          type
          glossaryNodeUri
          glossaryNodeName
          possibleValues
        }
      }
    }
  `
});
