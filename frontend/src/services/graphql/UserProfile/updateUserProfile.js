import { gql } from 'apollo-boost';

export const updateUserProfile = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation UpdateUserProfile($input: UserProfileInput!) {
      updateUserProfile(input: $input) {
        username
        bio
        b64EncodedAvatar
        tags
      }
    }
  `
});
