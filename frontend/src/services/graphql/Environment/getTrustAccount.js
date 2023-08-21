import { gql } from 'apollo-boost';

export const getTrustAccount = () => ({
  query: gql`
    query GetTrustAccount {
      getTrustAccount
    }
  `
});
