import { gql } from 'apollo-boost';

const deleteGlossary = (nodeUri) => ({
  variables: {
    nodeUri
  },
  mutation: gql`
    mutation deleteGlossary($nodeUri: String!) {
      deleteGlossary(nodeUri: $nodeUri)
    }
  `
});

export default deleteGlossary;
