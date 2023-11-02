import { ModuleNames, getModuleActiveStatus } from 'utils';

export const SharesModule = {
  name: 'shares',
  resolve_dependency: () => {
    return getModuleActiveStatus(ModuleNames.DATASETS);
  }
};

export { ShareInboxList } from './components';
