import { Box, Pagination } from '@mui/material';
import * as PropTypes from 'prop-types';

export function Pager(props) {
  const { items, mgTop, mgBottom, onChange } = props;
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        mt: mgTop || 6,
        mb: mgBottom || 0
      }}
    >
      <Pagination count={items.pages} page={items.page} onChange={onChange} />
    </Box>
  );
}

Pager.propTypes = {
  items: PropTypes.shape({
    pages: PropTypes.number,
    nodes: PropTypes.any,
    count: PropTypes.number,
    hasPrevious: PropTypes.bool,
    hasNext: PropTypes.bool,
    page: PropTypes.number
  }),
  mgTop: PropTypes.number,
  mgBottom: PropTypes.number,
  onChange: PropTypes.func
};
