import { gql } from 'apollo-boost';

export const getMaintenanceStatus = () => ({
  query: gql`
    query getMaintenanceWindowStatus {
      getMaintenanceWindowStatus {
        status
        mode
      }
    }
  `
});
