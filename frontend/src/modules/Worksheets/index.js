import { getModuleActiveStatus, ModuleNames } from 'utils';

export const WorksheetsModule = {
  moduleDefinition: true,
  name: 'worksheets',
  isEnvironmentModule: false,
  resolve_dependency: () => {
    return (
      getModuleActiveStatus(ModuleNames.DATASETS) &&
      getModuleActiveStatus(ModuleNames.WORKSHEETS)
    );
  }
};
