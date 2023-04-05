import { gql } from 'apollo-boost';

export const getMonitoringDashboardId = () => ({
  query: gql`
    query getMonitoringDashboardId {
      getMonitoringDashboardId
    }
  `
});
