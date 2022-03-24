import { gql } from 'apollo-boost';

const updateUserProfile = (input) => ({
  variables: {
    input
  },
  mutation: gql`mutation UpdateUserProfile($input:UserProfileInput!){
                updateUserProfile(input:$input){
                    username
                    bio
                    b64EncodedAvatar
                    tags
                }
            }
        `
});

export default updateUserProfile;
