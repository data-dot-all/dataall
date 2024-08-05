import { getModuleActiveStatus, ModuleNames } from 'utils';

export const S3TablesModule = {
  moduleDefinition: true,
  name: 's3_tables',
  isEnvironmentModule: false,
  resolve_dependency: () => {
    return getModuleActiveStatus(ModuleNames.S3_DATASETS);
  }
};
