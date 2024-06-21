import { gql } from 'apollo-boost';

export const reApplyShareObjectItemsOnDataset = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation reApplyShareObjectItemsOnDataset($input: datasetUri) {
      reApplyShareObjectItemsOnDataset(input: $input)
    }
  `
});
