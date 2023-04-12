import { gql } from 'apollo-boost';

export const deleteCategory = (nodeUri) => ({
  variables: {
    nodeUri
  },
  mutation: gql`
    mutation deleteCategory($nodeUri: String!) {
      deleteCategory(nodeUri: $nodeUri)
    }
  `
});
