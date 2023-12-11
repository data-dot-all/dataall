import { gql } from 'apollo-boost';

export const listGroups = ({ filter }) => ({
  variables: {
    filter
  },
  query: gql`
    query listGroups($filter: ServiceProviderGroupFilter) {
      listGroups(filter: $filter) {
        groupName
      }
    }
  `
});
