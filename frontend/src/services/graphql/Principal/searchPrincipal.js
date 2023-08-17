import { gql } from 'apollo-boost';

export const searchPrincipal = ({ filter }) => ({
  variables: {
    filter
  },
  query: gql`
    query SearchPrincipal($filter: PrincipalFilter) {
      searchPrincipal(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          principalId
          principalType
          principalName
          SamlGroupName
          environmentUri
          environmentName
          AwsAccountId
          region
          organizationUri
          organizationName
        }
      }
    }
  `
});
