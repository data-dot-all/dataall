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
import { LoadingButton } from '@mui/lab';
import useClient from '../../hooks/useClient';
import { SET_ERROR } from '../../store/errorReducer';
import { useDispatch } from '../../store';
import createDataPipelineEnvironment from '../../api/DataPipeline/createDataPipelineEnvironment';
import listEnvironmentGroups from '../../api/Environment/listEnvironmentGroups';
import * as Defaults from '../../components/defaults';

const PipelineEnvironmentCreateForm = (props) => {
  const { environmentOptions, triggerEnvSubmit, pipelineUri } = props;
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const client = useClient();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [kvEnvs, setKeyValueEnvs] = useState([]);
  const [mapGroups, setMapGroups] = useState(new Map())
  const [environmentOps, setEnvironmentOps] = useState(
    environmentOptions && environmentOptions.length > 0 ? environmentOptions : [{ environmentUri: 'someUri', label: 'some' },{ environmentUri: 'someUri', label: 'some2' }]
  );

  const fetchGroups = async (environment) => {
  try {
    console.log("FetchGroups")
    console.log(environment)
    const response = await client.query(
      listEnvironmentGroups({
        filter: Defaults.SelectListFilter,
        environmentUri: environment.environmentUri
      })
    );

    if (!response.errors) {
      setMapGroups(new Map(mapGroups.set(environment.environmentUri, response.data.listEnvironmentGroups.nodes)) )//Array of groups (Objects)
      console.log("Mapgroups")
      console.log(mapGroups)
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  } catch (e) {
    dispatch({ type: SET_ERROR, error: e.message });
  }
};

  const handleAddEnvRow = () => {
    if (kvEnvs.length <= 40) {
      const item = {
        stage: '',
        env: '',
        team: ''
      };
      setKeyValueEnvs((prevState) => [...prevState, item]);
    } else {
      dispatch({
        type: SET_ERROR,
        error: 'You cannot add more than 40 development stages'
      });
    }
  };

  const handleChange = (idx, field) => (e) => {
    console.log("inside handle change")
    const { value } = e.target;

    setKeyValueEnvs((prevstate) => {
      const rows = [...prevstate];
      if (field === 'stage') {
        rows[idx].stage = value;
      } else if (field === 'env'){
        rows[idx].environmentLabel = value.label;
        rows[idx].environmentUri = value.environmentUri;
        console.log("env")
        console.log(kvEnvs[idx].environmentUri)
        console.log(mapGroups)
        console.log(mapGroups.keys())
        console.log(mapGroups.get(kvEnvs[idx].environmentUri))
      } else{
        rows[idx].samlGroupName = value;
      }
      return rows;
    });
    console.log(kvEnvs)
    console.log(kvEnvs[idx])
  };

  const handleRemoveEnvRow = (idx) => {
    setKeyValueEnvs((prevstate) => {
      const rows = [...prevstate];
      rows.splice(idx, 1);
      return rows;
    });
  };

  async function submit(element, index) {
    console.log("element")
    console.log(element)
    console.log(pipelineUri)
    try {
      const response = await client.mutate(
        createDataPipelineEnvironment({
          input: {
            stage: element.stage,
            order: index+1,
            pipelineUri: pipelineUri,
            environmentLabel: element.environmentLabel,
            environmentUri: element.environmentUri,
            samlGroupName: element.samlGroupName

          }
        })
      );
      if (!response.errors) {
        console.log("submited env")
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (err) {
      console.error(err);
      dispatch({ type: SET_ERROR, error: err.message });
    }
  }

  useEffect(() => {
      if (client && triggerEnvSubmit && pipelineUri && kvEnvs.length > 0) {
        console.log("triggerNOW")
        console.log(pipelineUri)
        console.log(kvEnvs.length)
        console.log(kvEnvs)
        kvEnvs.forEach((element, index) => submit(element, index))
      }
      if (client && environmentOptions.length > 0) {
        console.log("initial fetch use effect")
        environmentOptions.forEach((element) => fetchGroups(element))
      }
    }, [client, dispatch, triggerEnvSubmit, pipelineUri, environmentOptions]);

  console.log(kvEnvs)

  return (
    <>
      <Grid container spacing={3}>
        <Grid item lg={12} xl={12} xs={12}>
          <Box>
            <Card>
              <CardHeader title="Development environments" />
              <Divider />
              <CardContent>
                <Box>
                  <Table size="small">
                    <colgroup>
                        <col width="5%" />
                        <col width="15%" />
                        <col width="40%" />
                        <col width="40%" />
                    </colgroup>
                    {kvEnvs && kvEnvs.length > 0 && (
                      <TableHead>
                        <TableRow>
                          <TableCell>Order</TableCell>
                          <TableCell>Development Stage</TableCell>
                          <TableCell>Environment</TableCell>
                          <TableCell>Team</TableCell>
                        </TableRow>
                      </TableHead>
                    )}
                    <TableBody>
                      {kvEnvs.map((item, idx) => (
                        <>
                          <TableRow id="addr0" key={item.uri}>
                            <TableCell>
                              <TextField
                                fullWidth
                                name="idx"
                                value={(idx+1).toString()}
                                variant="outlined"
                              />
                            </TableCell>
                            <TableCell>
                              <TextField
                                fullWidth
                                name="stage"
                                value={kvEnvs[idx].stage}
                                onChange={handleChange(idx, 'stage')}
                                variant="outlined"
                              />
                            </TableCell>
                            <TableCell>
                              <TextField
                                fullWidth
                                name="env"
                                value={kvEnvs[idx].environmentLabel}
                                onChange={handleChange(idx, 'env')}
                                select
                                variant="outlined"
                              >
                                {environmentOps.map((environment) => (
                                  <MenuItem
                                    key={environment.environmentUri}
                                    value={environment}
                                  >
                                    {environment.label}
                                  </MenuItem>
                                ))}
                              </TextField>
                            </TableCell>
                            <TableCell>
                              <TextField
                                fullWidth
                                name="team"
                                value={kvEnvs[idx].samlGroupName}
                                onChange={handleChange(idx, 'team')}
                                select
                                variant="outlined"
                              >
                                {mapGroups.get(kvEnvs[idx].environmentUri) && (mapGroups.get(kvEnvs[idx].environmentUri).map((g) => (
                                  <MenuItem
                                    key={g.groupUri}
                                    value={g.groupUri}
                                  >
                                    {g.groupUri}
                                  </MenuItem>
                                )))}
                              </TextField>
                            </TableCell>
                            <td>
                              <IconButton
                                onClick={() => {
                                  handleRemoveEnvRow(idx);
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
                    <Button type="button" onClick={handleAddEnvRow}>
                      Add environment
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
PipelineEnvironmentCreateForm.propTypes = {
  environmentOptions: PropTypes.array.isRequired,
  triggerEnvSubmit: PropTypes.bool.isRequired,
  pipelineUri: PropTypes.string.isRequired,
};
export default PipelineEnvironmentCreateForm;
