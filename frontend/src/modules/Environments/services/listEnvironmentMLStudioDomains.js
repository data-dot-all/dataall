import { gql } from 'apollo-boost';

export const listEnvironmentMLStudioDomains = ({ filter, environmentUri }) => ({
  variables: {
    environmentUri,
    filter
  },
  query: gql`
    query listEnvironmentMLStudioDomains(
      $filter: VpcFilter
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
          VpcId
          vpcUri
          label
          name
          default
          SamlGroupName
          publicSubnetIds
          privateSubnetIds
          region
        }
      }
    }
  `
});
