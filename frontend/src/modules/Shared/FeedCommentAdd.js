import SendIcon from '@mui/icons-material/Send';
import { Box, IconButton, TextField, Tooltip } from '@mui/material';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import { useState } from 'react';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { postFeedMessage, useClient } from 'services';

export const FeedCommentAdd = (props) => {
  const dispatch = useDispatch();
  const { targetType, targetUri, reloadMessages } = props;
  const [value, setValue] = useState('');
  const { enqueueSnackbar } = useSnackbar();
  const [rows, setRows] = useState(1);
  const client = useClient();

  const postMessage = async () => {
    const response = await client.mutate(
      postFeedMessage({
        targetUri,
        targetType,
        input: {
          content: value
        }
      })
    );
    if (!response.errors) {
      enqueueSnackbar('Message published', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
      reloadMessages();
      setValue('');
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  const handleChange = (event) => {
    setValue(event.target.value);
  };

  const handleInputKeyup = (event) => {
    if (event.code === 'Enter' && value) {
      postMessage().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  };

  return (
    <Box
      sx={{
        alignItems: 'center',
        display: 'flex',
        p: 1
      }}
    >
      <TextField
        FormHelperTextProps={{
          sx: {
            textAlign: 'right',
            mr: 0
          }
        }}
        fullWidth
        placeholder="Leave a message"
        multiline
        onChange={handleChange}
        onKeyDown={() => setRows(4)}
        rows={rows}
        value={value}
        variant="outlined"
        onKeyUp={handleInputKeyup}
      />
      <Tooltip title="Send">
        <IconButton
          color={value ? 'primary' : 'default'}
          component={value ? 'button' : 'span'}
          disabled={!value}
          onClick={postMessage}
        >
          <SendIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    </Box>
  );
};

FeedCommentAdd.propTypes = {
  targetUri: PropTypes.string.isRequired,
  targetType: PropTypes.string.isRequired,
  reloadMessages: PropTypes.func.isRequired
};
