import { gql } from 'apollo-boost';

export const listCognitoGroups = ({ filter }) => ({
  variables: {
    filter
  },
  query: gql`
    query listCognitoGroups($filter: CognitoGroupFilter) {
      listCognitoGroups(filter: $filter) {
        groupName
      }
    }
  `
});
