import { gql } from 'apollo-boost';

const listAssetLinkedTerms = ({ uri, filter }) => ({
  variables: {
    filter,
    uri
  },
  query: gql`
    query ListAssetLinkedTerms(
      $uri: String!
      $filter: GlossaryTermTargetFilter
    ) {
      listAssetLinkedTerms(uri: $uri, filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          linkUri
          nodeUri
          owner
          created
          approvedByOwner
          approvedBySteward
          term {
            label
            readme
            created
            owner
            glossary {
              label
              nodeUri
            }
            path
          }
        }
      }
    }
  `
});

export default listAssetLinkedTerms;
