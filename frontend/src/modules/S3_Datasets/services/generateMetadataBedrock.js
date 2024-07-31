import { gql } from 'apollo-boost';

export const generateMetadataBedrock = ({ resourceUri, type, version }) => ({
  variables: {
    resourceUri,
    type,
    version
  },
  mutation: gql`
    mutation generateMetadata(
      $resourceUri: String!
      $type: MetadataGenerationTargets
      $version: Int
    ) {
      generateMetadata(
        resourceUri: $resourceUri
        type: $type
        version: $version
      ) {
        Description
        Tags
        Topic
        Column_Descriptions {
          Column_Description
          Column_Name
        }
        TableName
      }
    }
  `
});
