import { gql } from 'apollo-boost';

export const getGroupsForUser = (userid) => {
  return {
    variables: {
      userid
    },
    query: gql`
      query getGroupsForUser($userid: String!) {
        getGroupsForUser(userid: $userid)
      }
    `
  };
};
