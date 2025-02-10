import { Tooltip } from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import PropTypes from 'prop-types';

export const InfoIconWithToolTip = (props) => {
  const { title, size, placement } = props;

  return (
    <Tooltip title={title} placement={placement}>
      <InfoIcon sx={{ fontSize: `${size}rem` }}></InfoIcon>
    </Tooltip>
  );
};

InfoIconWithToolTip.propTypes = {
  title: PropTypes.any,
  size: PropTypes.number,
  placement: PropTypes.string
};

InfoIconWithToolTip.defaultProps = {
  title: '',
  size: 1,
  placement: 'bottom'
};
