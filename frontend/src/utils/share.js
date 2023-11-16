export const generateShareItemLabel = (itemType): string => {
  switch (itemType) {
    case 'Table':
      return 'Table';
    case 'S3Bucket':
      return 'S3Bucket';
    case 'StorageLocation':
      return 'Folder';
  }
};
