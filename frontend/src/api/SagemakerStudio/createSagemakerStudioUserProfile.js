import { gql } from 'apollo-boost';

const createSagemakerStudioUserProfile = (input) => ({
  variables: {
    input
  },
  mutation: gql`mutation createSagemakerStudioUserProfile(
            $input:NewSagemakerStudioUserProfileInput,
        ){
            createSagemakerStudioUserProfile(input:$input){
                sagemakerStudioUserProfileUri
                name
                label
                created
                description
                tags
            }
        }`
});

export default createSagemakerStudioUserProfile;
