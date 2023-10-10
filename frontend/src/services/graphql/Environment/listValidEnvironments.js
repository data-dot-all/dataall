import gql from 'graphql-tag';

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
        }
      }
    }
  `
});
