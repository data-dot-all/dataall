import * as PropTypes from 'prop-types';
import Label from './Label';

const ShareStatus = (props) => {
  const { status } = props;
  const setTagColor = () => {
    if (['Approved', 'Share_Succeeded', 'Revoke_Share_Succeeded'].includes(status)) return 'success';
    if (['Rejected', 'Share_Failed', 'Revoke_Share_Failed'].includes(status))
      return 'error';
    if (['PendingApproval', 'PendingRevoke'].includes(status)) return 'warning';
    return 'info';
  };
  return <Label color={setTagColor(status)}>{status}</Label>;
};
ShareStatus.propTypes = {
  status: PropTypes.string.isRequired
};
export default ShareStatus;
