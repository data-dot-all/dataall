import { gql } from 'apollo-boost';

export const listUserForGroup = (groupUri) => ({
  variables: {
    groupUri
  },
  query: gql`
    query ListUsersForGroup($groupUri: String!) {
      listUsersForGroup(groupUri: $groupUri)
    }
  `
});
