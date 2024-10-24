import { gql } from 'apollo-boost';

export const getAttachedMetadataForm = (uri) => ({
  variables: {
    uri
  },
  query: gql`
    query getAttachedMetadataForm($uri: String!) {
      getAttachedMetadataForm(uri: $uri) {
        uri
        metadataForm {
          uri
          name
          description
          SamlGroupName
          visibility
          homeEntity
          homeEntityName
          userRole
        }
        version
        entityType
        entityUri
        fields {
          uri
          field {
            uri
            name
            description
            required
            type
            glossaryNodeUri
            glossaryNodeName
            possibleValues
            displayNumber
          }
          value
        }
      }
    }
  `
});
