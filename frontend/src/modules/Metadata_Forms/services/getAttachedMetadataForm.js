import { gql } from 'apollo-boost';

export const getAttachedMetadataForm = (uri) => ({
  variables: {
    uri
  },
  query: gql`
    query getAttachedMetadataForm($uri: String!) {
      getMetadataForm(uri: $uri) {
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
          }
          value
        }
      }
    }
  `
});
