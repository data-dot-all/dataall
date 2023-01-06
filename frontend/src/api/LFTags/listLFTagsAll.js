import { gql } from 'apollo-boost';

const listLFTagsAll = () => ({
  variables: {},
  query: gql`
    query listLFTagsAll {
      listLFTagsAll {
        LFTagKey
        LFTagValues
      }
    }
  `
});

export default listLFTagsAll;
