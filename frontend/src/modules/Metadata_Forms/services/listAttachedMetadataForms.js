import { gql } from 'apollo-boost';

export const listAttachedMetadataForms = (filter) => ({
  variables: {
    filter
  },
  query: gql`
    query listAttachedMetadataForms($filter: AttachedMetadataFormFilter) {
      listAttachedMetadataForms(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
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
          entityName
          entityOwner
        }
      }
    }
  `
});
