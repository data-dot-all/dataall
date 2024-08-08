import { gql } from 'apollo-boost';

export const deleteTableDataFilter = ({ filterUri }) => ({
  variables: {
    filterUri
  },
  mutation: gql`
    mutation deleteTableDataFilter($filterUri: String!) {
      deleteTableDataFilter(filterUri: $filterUri)
    }
  `
});
