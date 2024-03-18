import { gql } from 'apollo-boost';

export const listWarehouseConnections = ({ filter }) => ({
  variables: {
    filter
  },
  query: gql`
    query listWarehouseConnections($filter: WarehouseFilter) {
      listWarehouseConnections(filter: $filter) {
        count
        page
        pages
        hasNext
        hasPrevious
        nodes {
          connectionUri
          name
          warehouseId
          warehouseType
          SamlAdminGroupName
          connectionType
          connectionDetails
        }
      }
    }
  `
});
