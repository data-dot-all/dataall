import { gql } from 'apollo-boost';

const createLFTagShare = ({ lfTagKey, lfTagValue, input }) => {
  console.log('rcv', input);
  return {
    variables: {
      input,
      lfTagValue,
      lfTagKey
    },
    mutation: gql`
      mutation createLFTagShare(
        $lfTagKey: String!
        $lfTagValue: String!
        $input: NewLFTagShareInput
      ) {
        createLFTagShare(
          lfTagKey: $lfTagKey
          lfTagValue: $lfTagValue
          input: $input
        ) {
          lftagShareUri
          created
        }
      }
    `
  };
};

export default createLFTagShare;
