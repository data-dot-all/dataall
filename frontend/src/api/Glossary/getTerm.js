import { gql } from 'apollo-boost';

export const getTerm = ({ nodeUri }) => ({
  variables: {
    nodeUri
  },
  query: gql`
    query GetTerm($nodeUri: String!) {
      getTerm(nodeUri: $nodeUri) {
        nodeUri
        label
        readme
        created
        owner
        status
        path
        stats {
          categories
          terms
          associations
        }
        associations {
          count
          pages
          hasNext
          hasPrevious
          nodes {
            linkUri
            targetUri
            approvedByOwner
            approvedBySteward
            target {
              __typename
              ... on Dataset {
                label
              }
            }
          }
        }
      }
    }
  `
});
