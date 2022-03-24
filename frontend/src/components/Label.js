import PropTypes from 'prop-types';
import { experimentalStyled } from '@material-ui/core/styles';

const LabelRoot = experimentalStyled('span')((({ theme, styleProps }) => {
  const backgroundColor = theme.palette[styleProps.color].main;
  const color = theme.palette[styleProps.color].contrastText;

  return {
    alignItems: 'center',
    backgroundColor,
    borderRadius: theme.shape.borderRadius,
    color,
    cursor: 'default',
    display: 'inline-flex',
    flexGrow: 0,
    flexShrink: 0,
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.pxToRem(11),
    fontWeight: theme.typography.fontWeightMedium,
    justifyContent: 'center',
    letterSpacing: 0.5,
    minWidth: 20,
    paddingBottom: theme.spacing(0.5),
    paddingLeft: theme.spacing(1),
    paddingRight: theme.spacing(1),
    paddingTop: theme.spacing(0.5),
    textTransform: 'uppercase',
    whiteSpace: 'nowrap'
  };
}));

const Label = (props) => {
  const { color = 'primary', children, ...other } = props;

  const styleProps = { color };

  return (
    <LabelRoot
      styleProps={styleProps}
      {...other}
    >
      {children}
    </LabelRoot>
  );
};

Label.propTypes = {
  children: PropTypes.node,
  color: PropTypes.oneOf([
    'primary',
    'secondary',
    'error',
    'warning',
    'success'
  ])
};

export default Label;
