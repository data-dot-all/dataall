import { gql } from 'apollo-boost';

const startWorksheetQuery = ({ worksheetUri, input }) => ({
  variables: {
    worksheetUri,
    input
  },
  mutation: gql`mutation StartWorksheetQuery(
            $worksheetUri:String!,
            $input:WorksheetQueryInput!,
        ){
            startWorksheetQuery(worksheetUri:$worksheetUri,input:$input){
                AthenaQueryId
                Error
                Status
                DataScannedInBytes
                ElapsedTimeInMs
            }
        }`
});

export default startWorksheetQuery;
