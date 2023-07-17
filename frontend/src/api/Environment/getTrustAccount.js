import { gql } from 'apollo-boost';

const getTrustAccount = () => ({
  query: gql`
    query GetTrustAccount {
      getTrustAccount
    }
  `
});

export default getTrustAccount;
