import { gql } from 'apollo-boost';

const publishDatasetTableUpdate = ({ tableUri }) => ({
  variables: {
    tableUri
  },
  mutation: gql`mutation publishDatasetTableUpdate($tableUri:String!){
            publishDatasetTableUpdate(tableUri:$tableUri)
        }`
});

export default publishDatasetTableUpdate;
