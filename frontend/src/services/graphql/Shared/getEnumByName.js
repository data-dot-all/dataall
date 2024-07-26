import { gql } from 'apollo-boost';

export const getEnumByName = ({ enum_name }) => ({
  variables: {
    enum_name
  },
  query: gql`
    query ${enum_name}{
      ${enum_name}{
          name
          value
      }
    }
  `
});
