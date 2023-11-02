import { getModuleActiveStatus, ModuleNames } from 'utils';

export const CatalogsModule = {
  name: 'catalog',
  resolve_dependency: () => {
    return (
      getModuleActiveStatus(ModuleNames.DATASETS) ||
      getModuleActiveStatus(ModuleNames.DASHBOARDS)
    );
  }
};
