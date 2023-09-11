import PropTypes from 'prop-types';
import { makeStyles } from '@mui/styles';
import { Avatar } from '@mui/material';

const useStyles = makeStyles((theme) => ({
  primary: {
    color: theme.palette.primary.contrastText,
    backgroundColor: theme.palette.primary.main
  }
}));

export const TextAvatar = (props) => {
  const { name } = props;
  const classes = useStyles();
  return (
    <>
      {name && (
        <Avatar className={classes.primary}>{name[0].toUpperCase()}</Avatar>
      )}
    </>
  );
};

TextAvatar.propTypes = {
  name: PropTypes.string.isRequired
};
