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

const DatasetLFTagsForm = (props) => {
  const { handleDatasetLFTags } = props;
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const client = useClient();
  const [tagsDict, setTagsDict] = useState([]);
  const [lfTagOptions, setLFTagOptions] = useState({});

//   const fetchGroups = async (environment) => {
//   try {
//     const response = await client.query(
//       listEnvironmentGroups({
//         filter: Defaults.SelectListFilter,
//         environmentUri: environment.environmentUri
//       })
//     );

//     if (!response.errors) {
//       setMapGroups(new Map(mapGroups.set(environment.environmentUri, response.data.listEnvironmentGroups.nodes)) )//Array of groups (Objects)
//     } else {
//       dispatch({ type: SET_ERROR, error: response.errors[0].message });
//     }
//   } catch (e) {
//     dispatch({ type: SET_ERROR, error: e.message });
//   }
// };

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
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (e) {
      dispatch({ type: SET_ERROR, error: e.message });
    }
  };
  const handleLFTagChange = (idx, field) => (e) => {
    const { value } = e.target;
    console.log(value)
    console.log(lfTagOptions)
    console.log(Object.keys(lfTagOptions))
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

  // async function submit(element, index) {
  //   try {
  //     const response = await client.mutate(
  //       createDataPipelineEnvironment({
  //         input: {
  //           stage: element.stage,
  //           order: index+1,
  //           pipelineUri: pipelineUri,
  //           environmentLabel: element.environmentLabel,
  //           environmentUri: element.environmentUri,
  //           samlGroupName: element.samlGroupName

  //         }
  //       })
  //     );
  //     if (!response.errors) {
  //     } else {
  //       dispatch({ type: SET_ERROR, error: response.errors[0].message });
  //     }
  //   } catch (err) {
  //     console.error(err);
  //     dispatch({ type: SET_ERROR, error: err.message });
  //   }
  // }

  // useEffect(() => {
  //     if (client && triggerEnvSubmit && pipelineUri && kvEnvs.length > 0) {
  //       kvEnvs.forEach((element, index) => submit(element, index))
  //     }
  //     if (client && environmentOptions.length > 0) {
  //       environmentOptions.forEach((element) => fetchGroups(element))
  //     }
  //   }, [client, dispatch, triggerEnvSubmit, pipelineUri, environmentOptions]);
  useEffect(() => {
    if (client) {
      fetchLFTagValues().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
    }
  }, [client, dispatch]);


  useEffect(() => {
    if (tagsDict.length > 0){
      handleDatasetLFTags(tagsDict)
    } else{
      handleDatasetLFTags(tagsDict)
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
DatasetLFTagsForm.propTypes = {
  handleDatasetLFTags: PropTypes.func.isRequired
};

export default DatasetLFTagsForm;
