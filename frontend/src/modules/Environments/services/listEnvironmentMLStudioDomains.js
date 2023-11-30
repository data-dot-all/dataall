import { gql } from 'apollo-boost';

export const listEnvironmentMLStudioDomains = ({ filter, environmentUri }) => ({
  variables: {
    environmentUri,
    filter
  },
  query: gql`
    query listEnvironmentMLStudioDomains(
      $filter: SagemakerStudioDomainFilter
      $environmentUri: String!
    ) {
      listEnvironmentMLStudioDomains(
        environmentUri: $environmentUri
        filter: $filter
      ) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          sagemakerStudioUri
          environmentUri
          label
          vpcType
          vpcId
          subnetIds
          sagemakerStudioDomainName
        }
      }
    }
  `
});
