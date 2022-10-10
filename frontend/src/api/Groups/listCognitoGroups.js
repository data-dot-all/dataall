import { gql } from 'apollo-boost';

const listCognitoGroups = () => ({
  query: gql`
    query listCognitoGroups {
      listCognitoGroups{
        groupName
      }
    }
  `
});

export default listCognitoGroups;
