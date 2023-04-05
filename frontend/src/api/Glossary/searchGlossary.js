import { gql } from 'apollo-boost';

export const searchGlossary = (filter) => ({
  variables: {
    filter
  },
  query: gql`
    query SearchGlossary($filter: GlossaryNodeSearchFilter) {
      searchGlossary(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
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
  `
});
