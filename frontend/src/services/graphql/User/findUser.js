import { gql } from 'apollo-boost';

export const findUser = ({ userName, page, pageSize }) => ({
  variables: {
    userName,
    pageSize,
    page
  },
  query: gql`
    query FindUser($page: Int, $pageSize: Int, $userName: String) {
      FindUser(userName: $userName, page: $page, pageSize: $pageSize) {
        count
        page
        pageSize
        pages
        hasNext
        hasPrevious
        nodes {
          userName
          organizations
        }
      }
    }
  `
});
