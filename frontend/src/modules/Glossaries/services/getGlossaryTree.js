import { gql } from 'apollo-boost';

export const getGlossaryTree = ({ nodeUri, filter }) => ({
  variables: {
    nodeUri,
    filter
  },
  query: gql`
    query GetGlossaryTree(
      $nodeUri: String!
      $filter: GlossaryNodeSearchFilter
    ) {
      getGlossary(nodeUri: $nodeUri) {
        nodeUri
        label
        readme
        created
        owner
        status
        path
        admin
        deleted
        categories {
          count
          page
          pages
          hasNext
          hasPrevious
          nodes {
            nodeUri
            parentUri
            label
            readme
            stats {
              categories
              terms
            }
            status
            created
          }
        }
        tree(filter: $filter) {
          count
          hasNext
          hasPrevious
          page
          pages
          nodes {
            __typename
            ... on Glossary {
              nodeUri
              label
              readme
              created
              owner
              path
            }
            ... on Category {
              nodeUri
              label
              parentUri
              readme
              created
              owner
              path
            }
            ... on Term {
              nodeUri
              parentUri
              label
              readme
              created
              owner
              path
            }
          }
        }
      }
    }
  `
});
