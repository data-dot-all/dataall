import { getModuleActiveStatus, ModuleNames } from 'utils';

export const GlossariesModule = {
  moduleDefinition: true,
  name: 'glossaries',
  isEnvironmentModule: false,
  resolve_dependency: () => {
    return (
      getModuleActiveStatus(ModuleNames.S3_DATASETS) ||
      getModuleActiveStatus(ModuleNames.DASHBOARDS)
    );
  }
};
