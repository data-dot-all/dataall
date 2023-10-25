/* eslint-disable no-restricted-properties */
import config from '../../generated/config.json';

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
  NOTIFICATIONS: 'notifications'
};

function isModuleEnabled(module) {
  if (module === ModuleNames.CATALOG || module === ModuleNames.GLOSSARIES) {
    return (
      getModuleActiveStatus(ModuleNames.DATASETS) ||
      getModuleActiveStatus(ModuleNames.DASHBOARDS)
    );
  }
  if (module === ModuleNames.SHARES || module === ModuleNames.NOTIFICATIONS) {
    return getModuleActiveStatus(ModuleNames.DATASETS);
  }
  if (module === ModuleNames.WORKSHEETS) {
    return (
      getModuleActiveStatus(ModuleNames.DATASETS) &&
      getModuleActiveStatus(ModuleNames.WORKSHEETS)
    );
  }

  return getModuleActiveStatus(module);
}

function isAnyFeatureModuleEnabled() {
  return !!(
    isModuleEnabled(ModuleNames.PIPELINES) ||
    isModuleEnabled(ModuleNames.DASHBOARDS) ||
    isModuleEnabled(ModuleNames.MLSTUDIO) ||
    isModuleEnabled(ModuleNames.NOTEBOOKS)
  );
}

function getModuleActiveStatus(moduleKey) {
  if (
    config.modules &&
    config.modules[moduleKey] &&
    config.modules[moduleKey].active !== undefined
  ) {
    return config.modules[moduleKey].active;
  }
  return false;
}

function isFeatureEnabled(moduleKey, featureKey) {
  if (
    moduleKey === 'core' &&
    config.core.features !== undefined &&
    config.core.features[featureKey] !== undefined
  ) {
    return config.core.features[featureKey];
  } else if (
    getModuleActiveStatus(moduleKey) &&
    config.modules[moduleKey]['features'] !== undefined &&
    config.modules[moduleKey]['features'][featureKey] !== undefined
  ) {
    return config.modules[moduleKey]['features'][featureKey];
  }
  return false;
}

export {
  ModuleNames,
  isModuleEnabled,
  isAnyFeatureModuleEnabled,
  isFeatureEnabled
};
