import PropTypes from 'prop-types';
import React, { useEffect, useState } from 'react';
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
  TableRow
} from '@mui/material';
import useClient from '../../hooks/useClient';
import Scrollbar from '../../components/Scrollbar';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import KeyValueTagUpdateForm from './KeyValueTagUpdateForm';
import listKeyValueTags from '../../api/KeyValueTags/listKeyValueTags';
import PencilAlt from '../../icons/PencilAlt';

const KeyValueTagList = ({ targetUri, targetType }) => {
  const client = useClient();
  const dispatch = useDispatch();
  const [items, setItems] = useState([]);
  const [openUpdateForm, setOpenUpdateForm] = useState(false);
  const [loading, setLoading] = useState(null);

  const fetchItems = async () => {
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
  };

  const openUpdate = () => {
    setOpenUpdateForm(true);
  };

  const closeUpdate = () => {
    fetchItems().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    setOpenUpdateForm(false);
  };

  useEffect(() => {
    if (client) {
      fetchItems().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client]);

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
                  Add/Edit Tags
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
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {items.map((tag) => (
                            <TableRow>
                              <TableCell>{tag.key || '-'}</TableCell>
                              <TableCell>{tag.value || '-'}</TableCell>
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
