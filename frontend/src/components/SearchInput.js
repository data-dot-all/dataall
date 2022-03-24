import { Box, Card, Input } from '@material-ui/core';
import * as PropTypes from 'prop-types';
import SearchIcon from '../icons/Search';

function SearchInput(props) {
  const { onChange, onKeyUp, value } = props;
  return (
    <Card>
      <Box
        sx={{
          alignItems: 'center',
          display: 'flex',
          p: 2
        }}
      >
        <SearchIcon fontSize="small" />
        <Box
          sx={{
            flexGrow: 1,
            ml: 3
          }}
        >
          <Input
            disableUnderline
            fullWidth
            onChange={onChange}
            onKeyUp={onKeyUp}
            placeholder="Search"
            value={value}
          />
        </Box>
      </Box>
    </Card>
  );
}

SearchInput.propTypes = {
  onChange: PropTypes.func,
  onKeyUp: PropTypes.func,
  value: PropTypes.string
};

export default SearchInput;
