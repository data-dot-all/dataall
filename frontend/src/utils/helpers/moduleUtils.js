/* eslint-disable no-restricted-properties */
import * as modules from 'modules';
import config from '../../generated/config.json';

function isModuleEnabled(module) {
  if (hasDependencyModule(module)) {
    const resolvedModule = resolveModuleName(module);
    return resolvedModule.resolve_dependency();
  }
  return getModuleActiveStatus(module);
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

function resolveModuleName(module) {
  return Object.values(modules).find((_module) => _module.name === module);
}

function hasDependencyModule(module) {
  const resolvedModule = resolveModuleName(module);
  return typeof resolvedModule?.resolve_dependency === 'function';
}

function configKeysMap(obj) {
  const map = {};
  const otherModules = ['catalog', 'shares', 'glossaries'];
  for (const module of [...Object.keys(obj), ...otherModules]) {
    const upperCaseModule = module.toUpperCase();
    map[upperCaseModule] = module;
  }
  return map;
}

const ModuleNames = configKeysMap(config.modules);

export { ModuleNames, isModuleEnabled, getModuleActiveStatus };
