import { gql } from 'apollo-boost';

export const approveTermAssociation = (linkUri) => ({
  variables: {
    linkUri
  },
  mutation: gql`
    mutation ApproveTermAssociation($linkUri: String!) {
      approveTermAssociation(linkUri: $linkUri)
    }
  `
});
