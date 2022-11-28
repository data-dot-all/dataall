import { gql } from 'apollo-boost';

const deleteCategory = (nodeUri) => ({
  variables: {
    nodeUri
  },
  mutation: gql`
    mutation deleteCategory($nodeUri: String!) {
      deleteCategory(nodeUri: $nodeUri)
    }
  `
});

export default deleteCategory;
