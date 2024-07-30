import { ModuleNames, getModuleActiveStatus } from 'utils';

export const DatasetsBaseModule = {
  moduleDefinition: true,
  name: 'datasets_base',
  isEnvironmentModule: false,
  resolve_dependency: () => {
    return (
      getModuleActiveStatus(ModuleNames.S3_DATASETS) ||
      getModuleActiveStatus(ModuleNames.REDSHIFT_DATASETS)
    );
  }
};
