import { gql } from 'apollo-boost';

export const getPlatformReaderSession = (dashboardId) => ({
  variables: {
    dashboardId
  },
  query: gql`
    query getPlatformReaderSession($dashboardId: String!) {
      getPlatformReaderSession(dashboardId: $dashboardId)
    }
  `
});
