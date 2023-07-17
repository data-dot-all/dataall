import { gql } from 'apollo-boost';

const test = () => ({
  query: gql`
    query Test {
      test
    }
  `
});

export default test;
