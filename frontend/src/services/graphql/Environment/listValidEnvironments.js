import { gql } from 'apollo-boost';

export const listValidEnvironments = ({ filter }) => ({
  variables: {
    filter
  },
  query: gql`
    query ListValidEnvironments($filter: EnvironmentFilter) {
      listValidEnvironments(filter: $filter) {
        count
        nodes {
          environmentUri
          label
          region
          organization {
            organizationUri
            name
            label
          }
          networks {
            VpcId
            privateSubnetIds
            publicSubnetIds
          }
        }
      }
    }
  `
});
