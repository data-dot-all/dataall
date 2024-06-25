import VerifiedUserOutlinedIcon from '@mui/icons-material/VerifiedUserOutlined';
import GppBadOutlinedIcon from '@mui/icons-material/GppBadOutlined';
import PendingOutlinedIcon from '@mui/icons-material/PendingOutlined';
import DangerousOutlinedIcon from '@mui/icons-material/DangerousOutlined';
import * as PropTypes from 'prop-types';
import { Typography } from '@mui/material';
import { Label } from './Label';

export const ShareHealthStatus = (props) => {
  const { status, healthStatus, lastVerificationTime } = props;

  const isShared = ['Revoke_Failed', 'Share_Succeeded'].includes(status);
  const isHealthPending = ['PendingReApply', 'PendingVerify', null].includes(
    healthStatus
  );
  const setStatus = () => {
    if (!healthStatus) return 'Undefined';
    return healthStatus;
  };

  const setColor = () => {
    if (!healthStatus) return 'info';
    if (['Healthy'].includes(healthStatus)) return 'success';
    if (['Unhealthy'].includes(healthStatus)) return 'error';
    if (isHealthPending) return 'warning';
    return 'info';
  };

  const setIcon = () => {
    if (!healthStatus) return <DangerousOutlinedIcon color={setColor()} />;
    if (['Healthy'].includes(healthStatus))
      return <VerifiedUserOutlinedIcon color={setColor()} />;
    if (['Unhealthy'].includes(healthStatus))
      return <GppBadOutlinedIcon color={setColor()} />;
    if (['PendingReApply', 'PendingVerify'].includes(healthStatus))
      return <PendingOutlinedIcon color={setColor()} />;
    return <DangerousOutlinedIcon color={setColor()} />;
  };

  if (!isShared) {
    return (
      <Typography color="textSecondary" variant="subtitle2">
        {'Item is not Shared'}
      </Typography>
    );
  }

  return (
    <div style={{ display: 'flex', alignItems: 'left' }}>
      {setIcon()}
      <Label color={setColor()}>{setStatus().toUpperCase()} </Label>
      {!isHealthPending && (
        <Typography color="textSecondary" variant="subtitle2" noWrap>
          {(lastVerificationTime &&
            '(' +
              lastVerificationTime.substring(
                0,
                lastVerificationTime.indexOf('.')
              ) +
              ')') ||
            ''}
        </Typography>
      )}
    </div>
  );
};

ShareHealthStatus.propTypes = {
  status: PropTypes.string.isRequired,
  healthStatus: PropTypes.string,
  lastVerificationTime: PropTypes.string
};
