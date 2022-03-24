import { gql } from 'apollo-boost';

const updateColumnDescription = ({ columnUri, input }) => ({
  variables: {
    columnUri,
    input
  },
  mutation: gql`
            mutation updateDatasetTableColumn($columnUri:String!,$input:DatasetTableColumnInput){
                updateDatasetTableColumn(columnUri:$columnUri,input:$input){
                    columnUri
                    description
                }
            }
        `
});

export default updateColumnDescription;
