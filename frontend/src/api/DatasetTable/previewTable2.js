import { gql } from 'apollo-boost';

const previewTable2 = (tableUri) => ({
  variables: {
    tableUri
  },
  query: gql`
            query PreviewTable2($tableUri:String!){
                previewTable2(tableUri:$tableUri){
                    rows
                    fields
                }
            }
        `
});

export default previewTable2;
