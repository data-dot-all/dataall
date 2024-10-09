import * as PropTypes from 'prop-types';
import { Label } from './Label';

export const ShareStatus = (props) => {
  const { status } = props;
  const setTagColor = () => {
    if (
      [
        'Approved',
        'Share_Approved',
        'Revoke_Approved',
        'Share_Succeeded',
        'Revoke_Succeeded'
      ].includes(status)
    )
      return 'success';
    if (
      [
        'Rejected',
        'Revoked',
        'Share_Rejected',
        'Share_Failed',
        'Revoke_Failed'
      ].includes(status)
    )
      return 'error';
    if (
      [
        'PendingApproval',
        'Submitted',
        'Submitted_For_Extension',
        'PendingExtension'
      ].includes(status)
    )
      return 'warning';
    return 'info';
  };
  return <Label color={setTagColor(status)}>{status}</Label>;
};
ShareStatus.propTypes = {
  status: PropTypes.string.isRequired
};
