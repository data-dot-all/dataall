import { gql } from 'apollo-boost';

const removeLFTag = ({ lftagUri }) => ({
  variables: {
    lftagUri
  },
  mutation: gql`
    mutation removeLFTag(
      $lftagUri: String!
    ) {
      removeLFTag(
        lftagUri: $lftagUri
      )
    }
  `
});

export default removeLFTag;
