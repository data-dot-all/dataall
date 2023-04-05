import { gql } from 'apollo-boost';

export const removeUser = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation RemoveUser($input: RemoveOrganizationUserInput) {
      removeUser(input: $input)
    }
  `
});
