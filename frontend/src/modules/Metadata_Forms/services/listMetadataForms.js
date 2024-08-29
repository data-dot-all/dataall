import { gql } from 'apollo-boost';

export const listMetadataForms = (filter) => ({
  variables: {
    filter
  },
  query: gql`
    query listMetadataForms($filter: MetadataFormFilter) {
      listMetadataForms(filter: $filter) {
        hasTenantPermissions
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          uri
          name
          description
          SamlGroupName
          userRole
          visibility
          homeEntity
          homeEntityName
        }
      }
    }
  `
});
