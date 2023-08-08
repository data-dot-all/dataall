import { gql } from 'apollo-boost';

export const dismissTermAssociation = (linkUri) => ({
  variables: {
    linkUri
  },
  mutation: gql`
    mutation DismissTermAssociation($linkUri: String!) {
      dismissTermAssociation(linkUri: $linkUri)
    }
  `
});
