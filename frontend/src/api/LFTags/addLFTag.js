import { gql } from 'apollo-boost';

const addLFTag = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation addLFTag($input: AddLFTagInput!) {
      addLFTag(input: $input) {
        LFTagKey
        LFTagValues
      }
    }
  `
});

export default addLFTag;
