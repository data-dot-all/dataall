import { gql } from 'apollo-boost';
export const deleteOmicsRun = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation deleteOmicsRun($input: OmicsDeleteInput!) {
      deleteOmicsRun(input: $input)
    }
  `
});
