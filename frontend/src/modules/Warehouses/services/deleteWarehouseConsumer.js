import { gql } from 'apollo-boost';

export const deleteWarehouseConsumer = (consumerUri) => ({
  variables: {
    consumerUri
  },
  mutation: gql`
    mutation deleteWarehouseConsumer($consumerUri: String!) {
      deleteWarehouseConsumer(consumerUri: $consumerUri)
    }
  `
});
