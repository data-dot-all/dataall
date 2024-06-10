import { getModuleActiveStatus, ModuleNames } from 'utils';

export const NotificationsModule = {
  moduleDefinition: true,
  name: 'notifications',
  isEnvironmentModule: false,
  resolve_dependency: () => {
    return getModuleActiveStatus(ModuleNames.S3_DATASETS);
  }
};
