import { getModuleActiveStatus, ModuleNames } from 'utils';

export const GlossariesModule = {
  name: 'glossaries',
  resolve_dependency: () => {
    return (
      getModuleActiveStatus(ModuleNames.DATASETS) ||
      getModuleActiveStatus(ModuleNames.DASHBOARDS)
    );
  }
};
