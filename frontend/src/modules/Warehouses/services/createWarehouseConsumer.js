import { gql } from 'apollo-boost';

export const createWarehouseConsumer = (input) => {
  return {
    variables: {
      input
    },
    mutation: gql`
      mutation createWarehouseConsumer($input: NewWarehouseConsumerInput) {
        createWarehouseConsumer(input: $input) {
          consumerUri
        }
      }
    `
  };
};
