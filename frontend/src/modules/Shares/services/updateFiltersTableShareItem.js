import { gql } from 'apollo-boost';

export const updateFiltersTableShareItem = (input) => {
  return {
    variables: {
      input
    },
    mutation: gql`
      mutation updateFiltersTableShareItem(
        $input: ModifyFiltersTableShareItemInput!
      ) {
        updateFiltersTableShareItem(input: $input)
      }
    `
  };
};
