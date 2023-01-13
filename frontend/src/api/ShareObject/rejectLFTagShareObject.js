import { gql } from 'apollo-boost';

const rejectLFTagShareObject = ({ lftagShareUri }) => ({
  variables: {
    lftagShareUri
  },
  mutation: gql`
    mutation rejectLFTagShareObject($lftagShareUri: String!) {
      rejectLFTagShareObject(lftagShareUri: $lftagShareUri) {
        lftagShareUri
        status
      }
    }
  `
});

export default rejectLFTagShareObject;

