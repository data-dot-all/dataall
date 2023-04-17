export const listToTree = (data, options) => {
  options = options || {};
  const ID_KEY = options.idKey || 'id';
  const PARENT_KEY = options.parentKey || 'parent';
  const CHILDREN_KEY = options.childrenKey || 'children';

  const tree = [];
  const childrenOf = {};
  let item;
  let id;
  let parentId;

  for (let i = 0, { length } = data; i < length; i++) {
    item = data[i];
    id = item[ID_KEY];
    parentId = item[PARENT_KEY] || 0;
    // every item may have children
    childrenOf[id] = childrenOf[id] || [];
    // init its children
    item[CHILDREN_KEY] = childrenOf[id];
    if (parentId !== 0) {
      // init its parent's children object
      childrenOf[parentId] = childrenOf[parentId] || [];
      // push it into its parent's children object
      childrenOf[parentId].push(item);
    } else {
      tree.push(item);
    }
  }

  return tree;
};
