import { gql } from 'apollo-boost';

const submitLFTagApproval = ({ lftagShareUri }) => ({
  variables: {
    lftagShareUri
  },
  mutation: gql`
    mutation submitLFTagShareObject($lftagShareUri: String!) {
      submitLFTagShareObject(lftagShareUri: $lftagShareUri) {
        lftagShareUri
        status
      }
    }
  `
});

export default submitLFTagApproval;
