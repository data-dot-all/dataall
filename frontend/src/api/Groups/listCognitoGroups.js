import { gql } from 'apollo-boost';

const listCognitoGroups = () => ({
  variables: {
  },
  query: gql`
    query listCognitoGroups() {
      listCognitoGroups() {
      }
    }
  `
});

export default listCognitoGroups;
