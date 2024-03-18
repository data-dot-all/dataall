import { gql } from 'apollo-boost';

export const createWarehouseConnection = (input) => {
  return {
    variables: {
      input
    },
    mutation: gql`
      mutation createWarehouseConnection($input: NewWarehouseConnectionInput) {
        createWarehouseConnection(input: $input) {
          connectionUri
        }
      }
    `
  };
};
