import { getModuleActiveStatus, ModuleNames } from 'utils';

export const CatalogsModule = {
  moduleDefinition: true,
  name: 'catalog',
  isEnvironmentModule: false,
  resolve_dependency: () => {
    return (
      getModuleActiveStatus(ModuleNames.DATASETS) ||
      getModuleActiveStatus(ModuleNames.DASHBOARDS)
    );
  }
};
