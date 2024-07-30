import { gql } from 'apollo-boost';

export const deleteRedshiftConnection = ({ connectionUri }) => ({
  variables: {
    connectionUri
  },
  mutation: gql`
    mutation deleteRedshiftConnection($connectionUri: String!) {
      deleteRedshiftConnection(connectionUri: $connectionUri)
    }
  `
});
