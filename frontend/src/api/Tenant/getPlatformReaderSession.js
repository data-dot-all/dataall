import { gql } from 'apollo-boost';

const getPlatformReaderSession = (dashboardId) => ({
  variables: {
    dashboardId
  },
  query: gql`
    query getPlatformReaderSession($dashboardId: String) {
      getPlatformReaderSession(dashboardId: $dashboardId)
    }
  `
});

export default getPlatformReaderSession;
