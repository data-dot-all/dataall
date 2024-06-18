import { gql } from 'apollo-boost';

export const getReaderSession = (dashboardUri) => ({
  variables: {
    dashboardUri
  },
  query: gql`
    query GetReaderSession($dashboardUri: String!) {
      getReaderSession(dashboardUri: $dashboardUri)
    }
  `
});
