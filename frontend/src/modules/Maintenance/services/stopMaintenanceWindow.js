import { gql } from 'apollo-boost';

export const stopMaintenanceWindow = () => ({
  mutation: gql`
    mutation stopMaintenanceWindow {
      stopMaintenanceWindow
    }
  `
});
