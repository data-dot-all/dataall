import { gql } from 'apollo-boost';

const inviteUser = ({ organizationUri, userName, role }) => ({
  variables: {
    input: { organizationUri, userName, role: role || 'Member' }
  },
  mutation: gql`mutation InviteUser($input:NewOrganizationUserInput){
            inviteUser(input:$input){
                userName
                userRoleInOrganization
                created
            }
        }`
});

export default inviteUser;
