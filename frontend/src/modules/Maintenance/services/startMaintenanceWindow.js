import { gql } from 'apollo-boost';

export const startMaintenanceWindow = ({ mode }) => ({
  variables: { mode },
  mutation: gql`
    mutation startMaintenanceWindow($mode: String) {
      startMaintenanceWindow(mode: $mode)
    }
  `
});
