import { getModuleActiveStatus, ModuleNames } from 'utils';

export const WorksheetsModule = {
  name: 'worksheets',
  resolve_dependency: () => {
    return (
      getModuleActiveStatus(ModuleNames.DATASETS) &&
      getModuleActiveStatus(ModuleNames.WORKSHEETS)
    );
  }
};
