/* eslint-disable no-restricted-properties */
import config from '../generated/config.json';

const ModuleNames = {
  CATALOG: 'catalog',
  DATASETS: 'datasets',
  SHARES: 'shares',
  GLOSSARIES: 'glossaries',
  WORKSHEETS: 'worksheets',
  NOTEBOOKS: 'notebooks',
  MLSTUDIO: 'mlstudio',
  PIPELINES: 'datapipelines',
  DASHBOARDS: 'dashboards',
};

function isModuleEnabled(module) {

  if (module === ModuleNames.CATALOG) {
    return (getModuleActiveStatus(ModuleNames.DATASETS) || getModuleActiveStatus(ModuleNames.DASHBOARDS));
  }

  return getModuleActiveStatus(module);
}

function getModuleActiveStatus(moduleKey) {
  if (config.modules && config.modules[moduleKey] && config.modules[moduleKey].active !== undefined) {
    return config.modules[moduleKey].active;
  }
  return false;
}

export { ModuleNames, isModuleEnabled };
