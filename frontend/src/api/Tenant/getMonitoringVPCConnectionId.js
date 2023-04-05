import { gql } from 'apollo-boost';

export const getMonitoringVPCConnectionId = () => ({
  query: gql`
    query getMonitoringVPCConnectionId {
      getMonitoringVPCConnectionId
    }
  `
});
