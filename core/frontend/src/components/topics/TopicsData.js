const TopicsData = {
  Finances: 'Finances',
  HumanResources: 'HumanResources',
  Products: 'Products',
  Services: 'Services',
  Operations: 'Operations',
  Research: 'Research',
  Sales: 'Sales',
  Orders: 'Orders',
  Sites: 'Sites',
  Energy: 'Energy',
  Customers: 'Customers',
  Misc: 'Misc'
};

export default Object.keys(TopicsData).map((t) => ({ label: t, value: t }));
