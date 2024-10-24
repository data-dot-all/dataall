function isTenantUser(groups) {
  return groups && groups.includes('DAAdministrators');
}

export { isTenantUser };
