import { gql } from 'apollo-boost';

const updateUserRole = ({ organizationUri, userName, role }) => ({
  variables: {
    input: { organizationUri, userName, role: role || 'Member' }
  },
  mutation: gql`mutation UpdateUser($input:ModifyOrganizationUserInput){
            updateUser(input:$input){
                userName
                userRoleInOrganization
                created
            }
        }`
});

export default updateUserRole;
