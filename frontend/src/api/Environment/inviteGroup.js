import { gql } from 'apollo-boost';

const inviteGroupOnEnvironment = (input) => ({
  variables: {
    input
  },
  mutation: gql`mutation inviteGroupOnEnvironment($input:InviteGroupOnEnvironmentInput!){
            inviteGroupOnEnvironment(input:$input){
                environmentUri
            }
        }`
});

export default inviteGroupOnEnvironment;
