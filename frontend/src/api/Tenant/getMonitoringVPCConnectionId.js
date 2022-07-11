import { gql } from 'apollo-boost';

const getMonitoringVPCConnectionId = () => ({
  query: gql`
    query getMonitoringVPCConnectionId {
      getMonitoringVPCConnectionId
    }
  `
});

export default getMonitoringVPCConnectionId;
