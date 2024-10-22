import { gql } from 'apollo-boost';

export const getEntityMetadataFormPermissions = (entityUri) => ({
  variables: {
    entityUri
  },
  query: gql`
    query getEntityMetadataFormPermissions($entityUri: String!) {
      getEntityMetadataFormPermissions(entityUri: $entityUri)
    }
  `
});
