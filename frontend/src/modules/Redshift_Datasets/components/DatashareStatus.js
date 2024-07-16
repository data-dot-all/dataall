import * as PropTypes from 'prop-types';
import { Label } from 'design';

export const DatashareStatus = (props) => {
  const { status } = props;
  const setTagColor = () => {
    if (['COMPLETED'].includes(status)) return 'success';
    if (['REJECTED', 'DEAUTHORIZED'].includes(status)) return 'error';
    if (
      [
        'PENDING_AUTHORIZATION',
        'AUTHORIZED',
        'NOT_REGISTERED_IN_LF',
        'MISSING_GLUE_DATABASE'
      ].includes(status)
    )
      return 'warning';
    return 'info';
  };
  return <Label color={setTagColor(status)}>{status}</Label>;
};
DatashareStatus.propTypes = {
  status: PropTypes.string.isRequired
};
