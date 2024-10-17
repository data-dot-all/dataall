import { gql } from 'apollo-boost';

export const createAttachedMetadataForm = (formUri, input) => ({
  variables: {
    formUri,
    input
  },
  mutation: gql`
    mutation createAttachedMetadataForm(
      $formUri: String!
      $input: NewAttachedMetadataFormInput!
    ) {
      createAttachedMetadataForm(formUri: $formUri, input: $input) {
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
          }
          value
        }
      }
    }
  `
});
