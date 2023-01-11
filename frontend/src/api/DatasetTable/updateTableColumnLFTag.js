import { gql } from 'apollo-boost';

const updateTableColumnLFTag = ({ columnUri, input }) => ({
  variables: {
    columnUri,
    input
  },
  mutation: gql`
    mutation updateTableColumnLFTag(
      $columnUri: String!
      $input: DatasetTableColumnLFTagInput
    ) {
      updateTableColumnLFTag(columnUri: $columnUri, input: $input) {
        columnUri
        description
      }
    }
  `
});

export default updateTableColumnLFTag;
