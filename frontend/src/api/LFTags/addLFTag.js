import { gql } from 'apollo-boost';

const addLFTag = (input) => ({
  variables: {
    input
  },
  mutation: gql`
    mutation addLFTag($input: AddLFTagInput!) {
      addLFTag(input: $input) {
        LFTagName
        LFTagValues
      }
    }
  `
});

export default addLFTag;
