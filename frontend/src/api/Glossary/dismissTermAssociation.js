import { gql } from 'apollo-boost';

const dismissTermAssociation = (linkUri) => ({
  variables: {
    linkUri
  },
  mutation: gql`
    mutation DismissTermAssociation($linkUri: String!) {
      dismissTermAssociation(linkUri: $linkUri)
    }
  `
});

export default dismissTermAssociation;
