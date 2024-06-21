import { gql } from 'apollo-boost';

export const getS3ConsumptionData = ({ shareUri }) => ({
  variables: {
    shareUri
  },
  query: gql`
    query getS3ConsumptionData($shareUri: String!) {
      getS3ConsumptionData(shareUri: $shareUri) {
        s3AccessPointName
        sharedGlueDatabase
        s3bucketName
      }
    }
  `
});
