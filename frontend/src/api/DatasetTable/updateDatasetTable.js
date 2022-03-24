import { gql } from 'apollo-boost';

const updateDatasetTable = ({ tableUri, input }) => ({
  variables: {
    tableUri,
    input
  },
  mutation: gql`
            mutation UpdateDatasetTable($tableUri:String!,$input:ModifyDatasetTableInput!){
                updateDatasetTable(tableUri:$tableUri,input:$input){
                    tableUri
                }
            }
        `
});

export default updateDatasetTable;
