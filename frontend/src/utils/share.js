export const generateShareItemLabel = (itemType): string => {
  switch (itemType) {
    case 'Table':
      return 'GlueTable';
    case 'S3Bucket':
      return 'S3Bucket';
    case 'StorageLocation':
      return 'Folder';
    case 'RedshiftTable':
      return 'RedshiftTable';
  }
};
