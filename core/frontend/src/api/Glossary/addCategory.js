import { gql } from 'apollo-boost';

const createCategory = ({ input, parentUri }) => ({
  variables: {
    input,
    parentUri
  },
  mutation: gql`
    mutation CreateCategory($parentUri: String!, $input: CreateCategoryInput) {
      createCategory(parentUri: $parentUri, input: $input) {
        nodeUri
        label
        path
        readme
        created
        owner
      }
    }
  `
});

export default createCategory;
