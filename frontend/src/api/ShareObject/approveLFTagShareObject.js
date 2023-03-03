import { gql } from 'apollo-boost';

const approveLFTagShareObject = ({ lftagShareUri }) => ({
  variables: {
    lftagShareUri
  },
  mutation: gql`
    mutation approveLFTagShareObject($lftagShareUri: String!) {
      approveLFTagShareObject(lftagShareUri: $lftagShareUri) {
        lftagShareUri
        status
      }
    }
  `
});

export default approveLFTagShareObject;
