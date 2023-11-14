import { getModuleActiveStatus, ModuleNames } from 'utils';

export const NotificationsModule = {
  name: 'notifications',
  resolve_dependency: () => {
    return (
      getModuleActiveStatus(ModuleNames.DATASETS)
    );
  }
};
