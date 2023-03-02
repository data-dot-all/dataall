import { gql } from 'apollo-boost';

const getCreatePivotRole = () => ({
  query: gql`
    query getCreatePivotRole {
      getCreatePivotRole
    }
  `
});

export default getCreatePivotRole;
