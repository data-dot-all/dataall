import PropTypes from 'prop-types';
import { makeStyles } from '@material-ui/core/styles';
import { Avatar } from '@material-ui/core';

const useStyles = makeStyles((theme) => ({
  primary: {
    color: theme.palette.primary.contrastText,
    backgroundColor: theme.palette.primary.main
  }
}));

const TextAvatar = (props) => {
  const { name } = props;
  const classes = useStyles();
  return (
    <>
      {name && (
      <Avatar className={classes.primary}>
        {name[0].toUpperCase()}
      </Avatar>
      )}
    </>
  );
};

TextAvatar.propTypes = {
  name: PropTypes.string.isRequired
};

export default TextAvatar;
