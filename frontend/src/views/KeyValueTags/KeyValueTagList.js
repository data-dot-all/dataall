import PropTypes from 'prop-types';
import React, { useCallback, useEffect, useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardHeader,
  CircularProgress,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Switch
} from '@mui/material';
import useClient from '../../hooks/useClient';
import Scrollbar from '../../components/Scrollbar';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import { useSnackbar } from 'notistack';
import KeyValueTagUpdateForm from './KeyValueTagUpdateForm';
import listKeyValueTags from '../../api/KeyValueTags/listKeyValueTags';
import PencilAlt from '../../icons/PencilAlt';
import updateCascadingKeyValueTag from "../../api/KeyValueTags/updateCascadingKeyValueTag";

const KeyValueTagList = ({ targetUri, targetType }) => {
  const client = useClient();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const [items, setItems] = useState([]);
  const [openUpdateForm, setOpenUpdateForm] = useState(false);
  const [loading, setLoading] = useState(null);

  const fetchItems = useCallback(async () => {
    setLoading(true);
    const response = await client.query(
      listKeyValueTags(targetUri, targetType)
    );
    if (!response.errors) {
      setItems(response.data.listKeyValueTags);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, targetType, targetUri]);

  const openUpdate = () => {
    setOpenUpdateForm(true);
  };

  const closeUpdate = () => {
    fetchItems().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    setOpenUpdateForm(false);
  };

  const handleUpdateCascadingKeyValueTag = useCallback(
    async (tag) => {
      const response = await client.mutate(
        updateCascadingKeyValueTag(tag.tagUri, tag.targetUri, tag.targetType, tag.cascade)
      );
      if (!response.errors) {
        enqueueSnackbar('This tag will be added to all data.all stacks created in this environment', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    },
    [
      client,
      dispatch,
      enqueueSnackbar,
    ]
  );

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch, fetchItems]);

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <Box sx={{ mt: 3 }}>
      {items && (
        <Box>
          {openUpdateForm ? (
            <KeyValueTagUpdateForm
              targetType={targetType}
              targetUri={targetUri}
              tags={items.length > 0 ? items : [{ key: '', value: '' }]}
              closeUpdate={closeUpdate}
            />
          ) : (
            <Box>
              <Box display="flex" justifyContent="flex-end" sx={{ p: 1 }}>
                <Button
                  color="primary"
                  startIcon={<PencilAlt fontSize="small" />}
                  sx={{ m: 1 }}
                  variant="outlined"
                  onClick={openUpdate}
                >
                  Add/Edit Stack Tags
                </Button>
              </Box>
              {items && items.length > 0 && (
                <Card sx={{ mt: 2 }}>
                  <CardHeader title={<Box>Key-Value Tags</Box>} />
                  <Divider />
                  <Scrollbar>
                    <Box sx={{ minWidth: 600 }}>
                      <Table>
                        <TableHead>
                          <TableRow>
                            <TableCell>Key</TableCell>
                            <TableCell>Value</TableCell>
                            {targetType == 'environment' && (<TableCell>Cascade enabled</TableCell>)}
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {items.map((tag) => (
                            <TableRow>
                              <TableCell>{tag.key || '-'}</TableCell>
                              <TableCell>{tag.value || '-'}</TableCell>
                              {targetType == 'environment' && (<TableCell>
                                <Switch
                                      defaultChecked={tag.cascade}
                                      color="primary"
                                      onChange={handleUpdateCascadingKeyValueTag(tag)}
                                      edge="start"
                                      name="cascade"
                                      value={tag.cascade}
                                    />
                              </TableCell>)}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </Box>
                  </Scrollbar>
                </Card>
              )}
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
};

KeyValueTagList.propTypes = {
  targetType: PropTypes.string.isRequired,
  targetUri: PropTypes.string.isRequired
};

export default KeyValueTagList;
