export const Topics = [
  'Finances',
  'HumanResources',
  'Products',
  'Services',
  'Operations',
  'Research',
  'Sales',
  'Orders',
  'Sites',
  'Energy',
  'Customers',
  'Misc'
];

export const ConfidentialityList = ['Unclassified', 'Official', 'Secret'];

export const policyManagementInfoMap = {
  FULLY_MANAGED:
    'Data.all manages creating, maintaining and also attaching the policy',
  PARTIALLY_MANAGED:
    "Data.all will create the IAM policy but won't attach policy to your consumption role. With this option, data.all will indicate share to be unhealthy if the data.all created policy is not attached.",
  EXTERNALLY_MANAGED:
    'Data.all will create the IAM policy required for any share but it will be incumbent on role owners to attach it or use their own policy. With this option, data.all will not indicate the share to be unhealthy even if the policy is not attached.'
};
