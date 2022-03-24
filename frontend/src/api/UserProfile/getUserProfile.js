import { gql } from 'apollo-boost';

const getUserProfile = (username) => ({
  variables: {
    username
  },
  query: gql`
            query GetUserProfile($username:String){
                getUserProfile(username:$username){
                    username
                    bio
                    b64EncodedAvatar
                    tags
                }
            }
        `
});

export default getUserProfile;
