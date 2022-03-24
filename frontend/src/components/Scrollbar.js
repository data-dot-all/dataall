import 'simplebar/dist/simplebar.min.css';
import { forwardRef } from 'react';
import SimpleBar from 'simplebar-react';
import { experimentalStyled } from '@material-ui/core/styles';

const ScrollbarRoot = experimentalStyled(SimpleBar)``;

const Scrollbar = forwardRef((props, ref) => (
  <ScrollbarRoot
    ref={ref}
    {...props}
  />
));

export default Scrollbar;
