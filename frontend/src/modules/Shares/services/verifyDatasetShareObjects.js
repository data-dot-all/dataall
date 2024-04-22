import { gql } from 'apollo-boost';

export const verifyDatasetShareObjects = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation verifyDatasetShareObjects($input: ShareObjectSelectorInput) {
      verifyDatasetShareObjects(input: $input)
    }
  `
});
