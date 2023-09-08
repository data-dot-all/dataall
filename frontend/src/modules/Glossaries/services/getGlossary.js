import { gql } from 'apollo-boost';

export const getGlossary = (nodeUri) => ({
  variables: {
    nodeUri
  },
  query: gql`
    query GetGlossary($nodeUri: String!) {
      getGlossary(nodeUri: $nodeUri) {
        nodeUri
        label
        readme
        created
        owner
        status
        path
        admin
        userRoleForGlossary
        stats {
          categories
          terms
          associations
        }
      }
    }
  `
});
