import { gql } from 'apollo-boost';

const getReaderSession = (dashboardUri) => ({
  variables: {
    dashboardUri
  },
  query: gql`
    query GetReaderSession($dashboardUri: String) {
      getReaderSession(dashboardUri: $dashboardUri)
    }
  `
});

export default getReaderSession;
