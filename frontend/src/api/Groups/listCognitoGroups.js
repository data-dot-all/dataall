import { gql } from 'apollo-boost';

const listCognitoGroups = ({ filter }) => ({
  variables: {
    filter
  },
  query: gql`
    query listCognitoGroups (
      $filter: CognitoGroupFilter
    ) {
      listCognitoGroups (
        filter: $filter
      ){
        groupName
      }
    }
  `
});

export default listCognitoGroups;
