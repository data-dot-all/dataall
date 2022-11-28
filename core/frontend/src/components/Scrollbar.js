import 'simplebar/dist/simplebar.min.css';
import { forwardRef } from 'react';
import SimpleBar from 'simplebar-react';
import { styled } from '@mui/styles';

const ScrollbarRoot = styled(SimpleBar)``;

const Scrollbar = forwardRef((props, ref) => (
  <ScrollbarRoot ref={ref} {...props} />
));

export default Scrollbar;
