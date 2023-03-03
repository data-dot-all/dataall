import { gql } from 'apollo-boost';

const deleteLFTagShareObject = ({ lftagShareUri }) => ({
  variables: {
    lftagShareUri
  },
  mutation: gql`
    mutation deleteLFTagShareObject($lftagShareUri: String!) {
      deleteLFTagShareObject(lftagShareUri: $lftagShareUri)
    }
  `
});

export default deleteLFTagShareObject;
