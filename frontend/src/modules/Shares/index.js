import { ModuleNames, getModuleActiveStatus } from 'utils';

export const SharesModule = {
  moduleDefinition: true,
  name: 'shares',
  isEnvironmentModule: false,
  resolve_dependency: () => {
    return getModuleActiveStatus(ModuleNames.S3_DATASETS);
  }
};

export { ShareBoxList } from './components';
