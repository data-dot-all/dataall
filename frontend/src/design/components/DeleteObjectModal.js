import PropTypes from 'prop-types';
import { Box, Button, CardContent, Dialog, Typography } from '@mui/material';
import { FaTrash } from 'react-icons/fa';

export const DeleteObjectModal = (props) => {
  const {
    objectName,
    deleteMessage,
    onApply,
    onClose,
    open,
    deleteFunction,
    ...other
  } = props;

  return (
    <Dialog maxWidth="sm" fullWidth onClose={onClose} open={open} {...other}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h6"
        >
          Delete {objectName} ?
        </Typography>

        {deleteMessage && <Box sx={{ mt: 1 }}>{deleteMessage}</Box>}
        <CardContent>
          <Button
            fullWidth
            startIcon={<FaTrash size={15} />}
            color="error"
            type="submit"
            variant="contained"
            onClick={() => {
              deleteFunction();
            }}
          >
            Delete
          </Button>
        </CardContent>
      </Box>
    </Dialog>
  );
};

DeleteObjectModal.propTypes = {
  objectName: PropTypes.string.isRequired,
  deleteMessage: PropTypes.object,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  deleteFunction: PropTypes.func.isRequired,
  open: PropTypes.bool.isRequired
};
