import React, { useCallback, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { useSnackbar } from 'notistack';
import {
  Box,
  Dialog,
  Typography,
  Grid
} from '@mui/material';
import { LoadingButton } from '@mui/lab';
import { GroupAddOutlined } from '@mui/icons-material';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import useClient from '../../hooks/useClient';
import updateTableColumnLFTag from '../../api/DatasetTable/updateTableColumnLFTag';
import LFTagEditForm from '../Datasets/LFTagEditForm';


const TableColumnLFTagForm = (props) => {
  const { onClose, open, columnToEdit, reloadColumns, ...other } = props;
  const { enqueueSnackbar } = useSnackbar();
  const dispatch = useDispatch();
  const client = useClient();
  const [isSubmitting, setSubmitting] = useState(false);
  const [columnLFTags, setColumnLFTags] = useState([]);
  console.log(columnToEdit)

  async function submit() {
    try {
      const response = await client.mutate(updateTableColumnLFTag
        ({
          columnUri: columnToEdit.id,
          input: {
            lfTagKey: columnLFTags ? columnLFTags.map((c) => c.lfTagKey) : [],
            lfTagValue: columnLFTags ? columnLFTags.map((c) => c.lfTagValue) : []
          }
        })
      );
      if (!response.errors) {
        setSubmitting(false);
        enqueueSnackbar('LF Tag Assigned', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        if (reloadColumns) {
          reloadColumns();
        }
        if (onClose) {
          onClose();
        }
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (err) {
      console.error(err);
      setSubmitting(false);
      dispatch({ type: SET_ERROR, error: err.message });
    }
  }

  return (
    <Dialog maxWidth="lg" fullWidth onClose={onClose} open={open} {...other}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          Assign LF Tag to Column: {columnToEdit.name}
        </Typography>
        <Grid item lg={12} md={6} xs={12}>
          <Box sx={{ mt: 3 }}>
            <LFTagEditForm
              handleLFTags={setColumnLFTags}
              tagobject={columnToEdit}
            />
          </Box>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'flex-end',
              mt: 3
            }}
          >
            <LoadingButton
              color="primary"
              onClick={() => submit()}
              loading={isSubmitting}
              type="submit"
              variant="contained"
            >
              Assign LF Tags
            </LoadingButton>
          </Box>
        </Grid>
      </Box>
    </Dialog>
  );
};

TableColumnLFTagForm.propTypes = {
  onClose: PropTypes.func,
  open: PropTypes.bool.isRequired,
  columnToEdit: PropTypes.object.isRequired
  // reloadTags: PropTypes.func
};

export default TableColumnLFTagForm;
