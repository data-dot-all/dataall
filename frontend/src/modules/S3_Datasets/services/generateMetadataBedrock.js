import { gql } from 'apollo-boost';

export const generateMetadataBedrock = ({
  resourceUri,
  targetType,
  metadataTypes,
  version
}) => ({
  variables: {
    resourceUri,
    targetType,
    metadataTypes,
    version
  },
  mutation: gql`
    mutation generateMetadata(
      $resourceUri: String!
      $targetType: MetadataGenerationTargets
      $metadataTypes: [String]
      $version: Int
    ) {
      generateMetadata(
        resourceUri: $resourceUri
        targetType: $targetType
        metadataTypes: $metadataTypes
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
