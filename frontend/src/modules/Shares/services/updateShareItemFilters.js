import { gql } from 'apollo-boost';

export const updateShareItemFilters = (input) => {
  return {
    variables: {
      input
    },
    mutation: gql`
      mutation updateShareItemFilters(
        $input: ModifyFiltersTableShareItemInput!
      ) {
        updateShareItemFilters(input: $input)
      }
    `
  };
};
