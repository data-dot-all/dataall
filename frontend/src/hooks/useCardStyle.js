import { makeStyles } from '@material-ui/core/styles';

const useCardStyle = makeStyles((theme) => ({ card: {
  boxShadow: '0 8px 40px -12px rgba(0,0,0,0.3)',
  '&:hover': {
    backgroundColor: theme.palette.background.hover,
    border: `2px solid ${theme.palette.primary.main}`
  }
}
}));
export default useCardStyle;
