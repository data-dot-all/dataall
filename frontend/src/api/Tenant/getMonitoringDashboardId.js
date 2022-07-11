import { gql } from 'apollo-boost';

const getMonitoringDashboardId = () => ({
  query: gql`
    query getMonitoringDashboardId {
      getMonitoringDashboardId
    }
  `
});

export default getMonitoringDashboardId;
