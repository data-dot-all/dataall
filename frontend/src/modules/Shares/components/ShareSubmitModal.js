import PropTypes from 'prop-types';
import { Dialog } from '@mui/material';
import React from 'react';
import { ShareEditForm } from '../../Shared/Shares/ShareEditForm';

export const ShareSubmitModal = (props) => {
  const {
    share,
    onApply,
    onClose,
    open,
    submitFunction,
    client,
    dispatch,
    enqueueSnackbar,
    fetchItem,
    sharedItems,
    ...other
  } = props;

  return (
    <Dialog maxWidth="md" fullWidth open={open} {...other}>
      <ShareEditForm
        share={share}
        dispatch={dispatch}
        enqueueSnackbar={enqueueSnackbar}
        client={client}
        onApply={onApply}
        onCancel={onClose}
        showViewShare={false}
      ></ShareEditForm>
    </Dialog>
  );
};

ShareSubmitModal.propTypes = {
  share: PropTypes.object.isRequired,
  onApply: PropTypes.func,
  onClose: PropTypes.func,
  submitFunction: PropTypes.func.isRequired,
  open: PropTypes.bool.isRequired,
  sharedItems: PropTypes.any
};
