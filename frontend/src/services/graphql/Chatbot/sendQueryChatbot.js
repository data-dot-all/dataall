import { gql } from 'apollo-boost';

export const sendQueryChatbot = ({ queryString }) => {
  return {
    variables: {
      queryString
    },
    mutation: gql`
      mutation sendQueryChatbot($queryString: String!) {
        sendQueryChatbot(queryString: $queryString) {
          response
        }
      }
    `
  };
};
