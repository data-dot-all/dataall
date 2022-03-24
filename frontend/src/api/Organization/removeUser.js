import { gql } from 'apollo-boost';

const removeUser = ({ input }) => ({
  variables: {
    input
  },
  mutation: gql`mutation RemoveUser($input:RemoveOrganizationUserInput){
            removeUser(input:$input)
        }`
});

export default removeUser;
