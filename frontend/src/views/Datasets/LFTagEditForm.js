import React, { useEffect, useState } from 'react';
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
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField
} from '@mui/material';
import { DeleteOutlined } from '@mui/icons-material';
import PropTypes from 'prop-types';
import useClient from '../../hooks/useClient';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import listLFTagsAll from '../../api/LFTags/listLFTagsAll';

const LFTagEditForm = (props) => {
  const { handleLFTags, tagobject } = props;
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const client = useClient();
  const [tagsDict, setTagsDict] = useState([]);
  const [lfTagOptions, setLFTagOptions] = useState({});
  // const [loading, setLoading] = useState(true);

  const fetchLFTagValues = async () => {
    try {
      const response = await client.query(listLFTagsAll());
      if (!response.errors) {
        setLFTagOptions(() =>{
          let tagData = {}
          response.data.listLFTagsAll.map((lf) => tagData[lf.LFTagKey] = lf.LFTagValues);
          return tagData
        });
        console.log(lfTagOptions)
        if (tagobject.lfTagKey && tagobject.lfTagKey.length > 0) {
          tagobject.lfTagKey.map((k, idx) => handleSetLFTags(k, tagobject.lfTagValue[idx]))
        }
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
      // setLoading(false)
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
  };

  useEffect(() => {
    if (client && tagobject) {
      fetchLFTagValues().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, tagobject]);

  const handleLFTagChange = (idx, field) => (e) => {
    const { value } = e.target;
    setTagsDict((prevstate) => {
      const rows = [...prevstate];
      if (field === 'lfTagKey') {
        rows[idx].lfTagValue = '';        
        rows[idx].lfTagKey = value;
      } else{
        rows[idx].lfTagValue = value;
      }
      return rows;
    });
  };

  const handleSetLFTags = (tagkey, tagval) => {
    console.log(tagkey)
    console.log(tagval)
    const item = {
      lfTagValue: tagval,
      lfTagKey: tagkey
    };
    setTagsDict((prevState) => [...prevState, item]);
  };

  const handleRemoveLFTagRow = (idx) => {
    setTagsDict((prevstate) => {
      const rows = [...prevstate];
      rows.splice(idx, 1);
      return rows;
    });
  };

  const handleAddLFTagRow = () => {
    const item = {
      lfTagValue: '',
      lfTagKey: ''
    };
    setTagsDict((prevState) => [...prevState, item]);
  };

  useEffect(() => {
    if (tagsDict.length >= 0){
      handleLFTags(tagsDict)
    } else{
      handleLFTags(tagsDict)
    }
  }, [tagsDict]);

  return (
    <>
      <Grid container spacing={3}>
        <Grid item lg={12} xl={12} xs={12}>
          <Box>
            <Card>
              <CardHeader title="LFTags (Optional)" />
              <Divider />
              <CardContent>
                <Box>
                  <Table size="small">
                    <colgroup>
                        <col width="40%" />
                        <col width="60%" />
                    </colgroup>
                    {tagsDict && tagsDict.length > 0 && (
                      <TableHead>
                        <TableRow>
                          <TableCell>LF Tag Keys</TableCell>
                          <TableCell>LF Tag Values</TableCell>
                        </TableRow>
                      </TableHead>
                    )}
                    <TableBody>
                      {tagsDict.map((item, idx) => (
                        <>
                          <TableRow id="addr0">
                            <TableCell>
                              <TextField
                                fullWidth
                                label="LF-Tag Key"
                                name="lfTagKey"
                                onChange={handleLFTagChange(idx, 'lfTagKey')}
                                select
                                value={tagsDict[idx].lfTagKey}
                                variant="outlined"
                              >
                                {Object.keys(lfTagOptions).map((lf) => (
                                  <MenuItem
                                    key={lf}
                                    value={lf}
                                  >
                                    {lf}
                                  </MenuItem>
                                ))}
                              </TextField>
                            </TableCell>
                            <TableCell>
                              <TextField
                                fullWidth
                                label="LF-Tag Value"
                                name="lfTagValue"
                                onChange={handleLFTagChange(idx, 'lfTagValue')}
                                select
                                value={tagsDict[idx].lfTagValue}
                                variant="outlined"
                              >
                                {tagsDict[idx].lfTagKey ?
                                lfTagOptions[tagsDict[idx].lfTagKey].map((tagVals) => (
                                  <MenuItem
                                    key={tagVals}
                                    value={tagVals}
                                  >
                                    {tagVals}
                                  </MenuItem>
                                )) 
                                : <MenuItem />
                                }
                              </TextField>
                            </TableCell>
                            <td>
                              <IconButton
                                onClick={() => {
                                  handleRemoveLFTagRow(idx);
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
                    <Button type="button" onClick={handleAddLFTagRow}>
                      Add LF Tag
                    </Button>
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
LFTagEditForm.propTypes = {
  handleLFTags: PropTypes.func.isRequired,
  tagobject: PropTypes.object.isRequired
};
export default LFTagEditForm;
