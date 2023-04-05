import { gql } from 'apollo-boost';

export const test = () => ({
  query: gql`
    query Test {
      test
    }
  `
});
