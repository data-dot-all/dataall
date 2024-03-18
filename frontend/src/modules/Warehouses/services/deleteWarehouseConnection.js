import { gql } from 'apollo-boost';

export const deleteWarehouseConnection = (connectionUri) => ({
  variables: {
    connectionUri
  },
  mutation: gql`
    mutation deleteWarehouseConnection($connectionUri: String!) {
      deleteWarehouseConnection(connectionUri: $connectionUri)
    }
  `
});
