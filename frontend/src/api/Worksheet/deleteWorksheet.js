import { gql } from 'apollo-boost';

const deleteWorksheet = (worksheetUri) => ({
  variables: {
    worksheetUri
  },
  mutation: gql`mutation deleteWorksheet(
            $worksheetUri:String!
        ){
            deleteWorksheet(worksheetUri:$worksheetUri)
        }`
});

export default deleteWorksheet;
