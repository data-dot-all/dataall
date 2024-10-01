import { gql } from 'apollo-boost';

export const generateMetadataBedrock = ({
  resourceUri,
  targetType,
  metadataTypes,
  version,
  sampleData
}) => ({
  variables: {
    resourceUri,
    targetType,
    metadataTypes,
    version,
    sampleData
  },
  mutation: gql`
    mutation generateMetadata(
      $resourceUri: String!
      $targetType: MetadataGenerationTargets
      $metadataTypes: [String]
      $version: Int
      $sampleData: SampleDataInput
    ) {
      generateMetadata(
        resourceUri: $resourceUri
        targetType: $targetType
        metadataTypes: $metadataTypes
        version: $version
        sampleData: $sampleData
      ) {
        type
        label
        description
        tags
        topics
        name
        subitem_descriptions {
          description
          label
          subitem_id
        }
      }
    }
  `
});
