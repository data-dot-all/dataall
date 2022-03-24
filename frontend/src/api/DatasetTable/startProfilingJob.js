import { gql } from 'apollo-boost';

const startProfilingJob = (tableUri) => ({
  variables: {
    tableUri
  },
  mutation: gql`mutation StartProfilingJob($tableUri:String!){
            startProfilingJob(tableUri:$tableUri){
                jobUri
            }
        }`
});

export default startProfilingJob;
