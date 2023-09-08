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
        associations {
          count
          page
          pages
          hasNext
          hasPrevious
          nodes {
            __typename
            target {
              ... on Dataset {
                label
              }
              ... on DatasetTable {
                label
              }
              ... on DatasetStorageLocation {
                label
              }
            }
          }
        }
      }
    }
  `
});
