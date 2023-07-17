import React, { useState } from 'react';
import { useSnackbar } from 'notistack';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Grid,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Switch
} from '@mui/material';
import { DeleteOutlined } from '@mui/icons-material';
import PropTypes from 'prop-types';
import { LoadingButton } from '@mui/lab';
import useClient from '../../hooks/useClient';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import updateKeyValueTags from '../../api/KeyValueTags/updateKeyValueTags';

const KeyValueTagUpdateForm = (props) => {
  const { targetType, targetUri, tags, closeUpdate } = props;
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const client = useClient();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [kvTags, setKeyValueTags] = useState(
    tags && tags.length > 0 ? tags : [{ key: '', value: '', cascade: false}]
  );

  const handleAddKeyValueRow = () => {
    if (kvTags.length <= 40) {
      const item = {
        key: '',
        value: '',
        cascade: false
      };
      setKeyValueTags((prevState) => [...prevState, item]);
    } else {
      dispatch({
        type: SET_ERROR,
        error: 'You cannot add more than 40 Key Value Tags'
      });
    }
  };

  const handleKeyValueChange = (idx, field) => (e) => {
    const { value } = e.target;
    setKeyValueTags((prevstate) => {
      const rows = [...prevstate];
      if (field === 'key') {
        rows[idx].key = value;
      } else if (field === 'value') {
        rows[idx].value = value;
      } else {
        rows[idx].cascade = e.target.checked;
      }
      return rows;
    });
  };

  const handleRemoveKeyValueRow = (idx) => {
    setKeyValueTags((prevstate) => {
      const rows = [...prevstate];
      rows.splice(idx, 1);
      return rows;
    });
  };

  async function submit() {
    setIsSubmitting(true);
    try {
      const response = await client.mutate(
        updateKeyValueTags({
          targetUri,
          targetType,
          tags:
            kvTags.length > 0
              ? kvTags.map((k) => ({ key: k.key, value: k.value, cascade: k.cascade }))
              : []
        })
      );
      if (!response.errors) {
        enqueueSnackbar('Key-Value tags saved', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        if (closeUpdate) {
          closeUpdate();
        }
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (err) {
      console.error(err);
      dispatch({ type: SET_ERROR, error: err.message });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <Grid container spacing={3}>
        <Grid item lg={12} xl={12} xs={12}>
          <Box>
            <Card>
              <CardHeader title="Key-Value Stack Tags" />
              <Divider />
              <CardContent>
                <Box>
                  <Table size="small">
                    {kvTags && kvTags.length > 0 && (
                      <TableHead>
                        <TableRow>
                          <TableCell>Key</TableCell>
                          <TableCell>Value</TableCell>
                          {targetType == 'environment' && (<TableCell>Cascade enabled</TableCell>)}
                        </TableRow>
                      </TableHead>
                    )}
                    <TableBody>
                      {kvTags.map((item, idx) => (
                        <>
                          <TableRow id="addr0" key={item.tagUri}>
                            <TableCell>
                              <TextField
                                fullWidth
                                name="key"
                                value={kvTags[idx].key}
                                onChange={handleKeyValueChange(idx, 'key')}
                                variant="outlined"
                              />
                            </TableCell>
                            <TableCell>
                              <TextField
                                fullWidth
                                name="value"
                                value={kvTags[idx].value}
                                onChange={handleKeyValueChange(idx, 'value')}
                                variant="outlined"
                              />
                            </TableCell>
                            {targetType == 'environment' && (<TableCell>
                                <Switch
                                      color="primary"
                                      edge="start"
                                      name="cascade"
                                      checked={kvTags[idx].cascade}
                                      value={kvTags[idx].cascade}
                                      onChange={handleKeyValueChange(idx, 'cascade')}
                                    />
                              </TableCell>)}
                            <td>
                              <IconButton
                                onClick={() => {
                                  handleRemoveKeyValueRow(idx);
                                }}
                              >
                                <DeleteOutlined fontSize="small" />
                              </IconButton>
                            </td>
                          </TableRow>
                        </>
                      ))}
                    </TableBody>
                  </Table>
                  <Box>
                    <Button type="button" onClick={handleAddKeyValueRow}>
                      Add Stack Tag
                    </Button>
                  </Box>
                  <Box display="flex" justifyContent="flex-end" sx={{ p: 1 }}>
                    <Button
                      color="primary"
                      sx={{ m: 1 }}
                      variant="outlined"
                      onClick={closeUpdate}
                    >
                      Cancel
                    </Button>
                    <LoadingButton
                      color="primary"
                      loading={isSubmitting}
                      onClick={() => submit()}
                      sx={{ m: 1 }}
                      variant="contained"
                    >
                      Save
                    </LoadingButton>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
        </Grid>
      </Grid>
    </>
  );
};

KeyValueTagUpdateForm.propTypes = {
  targetType: PropTypes.string.isRequired,
  targetUri: PropTypes.string.isRequired,
  tags: PropTypes.array.isRequired,
  closeUpdate: PropTypes.func.isRequired
};
export default KeyValueTagUpdateForm;
