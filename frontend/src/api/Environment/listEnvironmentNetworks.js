import { gql } from 'apollo-boost';

const listEnvironmentNetworks = ({ filter, environmentUri }) => ({
  variables: {
    environmentUri,
    filter
  },
  query: gql`
    query listEnvironmentNetworks(
      $filter: VpcFilter
      $environmentUri: String!
    ) {
      listEnvironmentNetworks(
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

export default listEnvironmentNetworks;
