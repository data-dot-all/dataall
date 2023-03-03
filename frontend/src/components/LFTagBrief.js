import PropTypes from 'prop-types';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Typography,
  Divider
} from '@mui/material';

const LFTagBrief = (props) => {
  const {
    title,
    lftagkeys,
    lftagvalues,
    objectType,
    ...other
  } = props;
  console.log(lftagkeys);
  console.log(lftagvalues);

  return (
    <Card {...other}>
      {title && (
        <Box>
          <CardHeader title={title} />
          <Divider />
        </Box>
      )}
      <CardContent>
        <Box sx={{ mt: 1 }}>
          {lftagkeys &&
            lftagkeys.map((key, idx) => (
              <Chip
                sx={{ mr: 0.5, mb: 0.5 }}
                key={key+"="+lftagvalues[idx]}
                label={key+"="+lftagvalues[idx]}
                variant="outlined"
              />
            ))}
        </Box>
      </CardContent>
    </Card>
  );
};

LFTagBrief.propTypes = {
  title: PropTypes.string.isRequired,
  lftagkeys: PropTypes.arrayOf(PropTypes.string),
  lftagvalues: PropTypes.arrayOf(PropTypes.string),
  objectType: PropTypes.string.isRequired
};

export default LFTagBrief;
