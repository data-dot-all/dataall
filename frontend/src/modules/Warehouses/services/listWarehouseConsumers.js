import { gql } from 'apollo-boost';

export const listWarehouseConsumers = ({ filter }) => ({
  variables: {
    filter
  },
  query: gql`
    query listWarehouseConsumers($filter: WarehouseFilter) {
      listWarehouseConsumers(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          consumerUri
          name
          warehouseId
          warehouseType
          SamlAdminGroupName
          consumerType
          consumerDetails
        }
      }
    }
  `
});
