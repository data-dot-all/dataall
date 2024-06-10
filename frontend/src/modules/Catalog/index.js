import { getModuleActiveStatus, ModuleNames } from 'utils';

export const CatalogsModule = {
  moduleDefinition: true,
  name: 'catalog',
  isEnvironmentModule: false,
  resolve_dependency: () => {
    return (
      getModuleActiveStatus(ModuleNames.S3_DATASETS) ||
      getModuleActiveStatus(ModuleNames.DASHBOARDS) ||
      getModuleActiveStatus(ModuleNames.DATASETS_BASE)
    );
  }
};
