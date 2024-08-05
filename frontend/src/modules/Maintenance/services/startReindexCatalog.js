import { gql } from 'apollo-boost';

export const startReindexCatalog = ({ handleDeletes }) => ({
  variables: { handleDeletes },
  mutation: gql`
    mutation startReindexCatalog($handleDeletes: Boolean!) {
      startReindexCatalog(handleDeletes: $handleDeletes)
    }
  `
});
