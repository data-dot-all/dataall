import { gql } from 'apollo-boost';

const pollWorksheetQuery = ({ worksheetUri, AthenaQueryId }) => ({
  variables: {
    worksheetUri,
    AthenaQueryId
  },
  query: gql`
    query PollWorksheetQuery($worksheetUri: String!, $AthenaQueryId: String!) {
      pollWorksheetQuery(
        worksheetUri: $worksheetUri
        AthenaQueryId: $AthenaQueryId
      ) {
        AthenaQueryId
        Status
        Error
        ElapsedTimeInMs
        DataScannedInBytes
        rows {
          cells {
            value
            typeName
            columnName
          }
        }
        columns {
          columnName
          typeName
        }
      }
    }
  `
});

export default pollWorksheetQuery;
