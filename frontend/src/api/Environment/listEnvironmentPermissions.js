import { gql } from 'apollo-boost';

const listEnvironmentGroupInvitationPermissions = ({ environmentUri }) => ({
  variables: {
    environmentUri
  },
  query: gql`
            query listEnvironmentGroupInvitationPermissions($environmentUri:String){
                listEnvironmentGroupInvitationPermissions(environmentUri:$environmentUri){
                    permissionUri
                    name
                    description
                }
            }
        `
});

export default listEnvironmentGroupInvitationPermissions;
