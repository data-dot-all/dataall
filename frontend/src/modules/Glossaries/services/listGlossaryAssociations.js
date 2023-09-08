import { gql } from 'apollo-boost';

export const listGlossaryAssociations = ({ nodeUri, filter }) => ({
  variables: {
    nodeUri,
    filter
  },
  query: gql`
    query GetGlossaryTree(
      $nodeUri: String!
      $filter: GlossaryTermTargetFilter
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
        userRoleForGlossary
        associations(filter: $filter) {
          count
          page
          pages
          hasNext
          hasPrevious
          nodes {
            linkUri
            targetUri
            approvedBySteward
            term {
              label
              nodeUri
            }
            targetType
            target {
              label
            }
          }
        }
      }
    }
  `
});
