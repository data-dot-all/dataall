import { gql } from 'apollo-boost';

const updateGlossary = ({ input, nodeUri }) => ({
  variables: {
    input,
    nodeUri
  },
  mutation: gql`
    mutation UpdateGlossary($nodeUri: String!, $input: UpdateGlossaryInput) {
      updateGlossary(nodeUri: $nodeUri, input: $input) {
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

export default updateGlossary;
