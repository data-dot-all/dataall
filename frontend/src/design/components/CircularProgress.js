import PropTypes from 'prop-types';
import { styled } from '@mui/styles';

const CircularProgressRoot = styled('div')({
  height: 56,
  width: 56
});

const CircularProgressBackground = styled('path')(({ theme }) => ({
  fill: 'none',
  stroke:
    theme.palette.mode === 'dark' ? 'rgba(0,0,0,0.15)' : 'rgba(0,0,0,0.05)',
  strokeWidth: 4
}));

const CircularProgressValue = styled('path')(({ theme }) => ({
  animation: '$progress 1s ease-out forwards',
  fill: 'none',
  stroke: theme.palette.primary.main,
  strokeWidth: 4,
  '@keyframes progress': {
    '0%': {
      strokeDasharray: '0 100'
    }
  }
}));

export const CircularProgress = (props) => {
  const { value, ...other } = props;

  return (
    <CircularProgressRoot {...other}>
      <svg viewBox="0 0 36 36">
        <CircularProgressBackground
          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          strokeDasharray="100, 100"
        />
        <CircularProgressValue
          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          strokeDasharray={`${value}, 100`}
        />
      </svg>
    </CircularProgressRoot>
  );
};

CircularProgress.propTypes = {
  value: PropTypes.number.isRequired
};
