import * as PropTypes from 'prop-types';
import { Label } from './Label';

export const StackStatus = (props) => {
  const { status } = props;
  const statusColor = (s) => {
    let color;
    switch (s) {
      case 'CREATE_COMPLETE':
      case 'UPDATE_COMPLETE':
        color = 'success';
        break;
      case 'CREATE_FAILED':
      case 'ProcessFailed':
      case 'DELETE_FAILED':
      case 'DELETE_COMPLETE':
      case 'ROLLBACK_COMPLETE':
      case 'ROLLBACK_IN_PROGRESS':
        color = 'error';
        break;
      default:
        color = 'info';
    }
    return color;
  };
  return <Label color={statusColor(status)}>{status}</Label>;
};
StackStatus.propTypes = {
  status: PropTypes.string.isRequired
};
