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

const PipelineEnvironmentUpdateForm = (props) => {
  const { environmentOptions,UpdateEnvstoParent } = props;
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const client = useClient();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [kvEnvs, setKeyValueEnvs] = useState([{ stage: '', label: '' }]
  );
  const [environmentOps, setEnvironmentOps] = useState(
    environmentOptions && environmentOptions.length > 0 ? environmentOptions : [{ environmentUri: 'some', label: 'some' }]
  );

  const handleAddEnvRow = () => {
    if (kvEnvs.length <= 40) {
      const item = {
        stage: '',
        label: ''
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
    console.log (value)
    setKeyValueEnvs((prevstate) => {
      const rows = [...prevstate];
      if (field === 'stage') {
        rows[idx].stage = value;
      } else {
        rows[idx].label = value;
      }
      return rows;
    });
  };

  const handleRemoveEnvRow = (idx) => {
    setKeyValueEnvs((prevstate) => {
      const rows = [...prevstate];
      rows.splice(idx, 1);
      return rows;
    });
  };

  console.log(environmentOptions)
  console.log(environmentOps)
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
                    {kvEnvs && kvEnvs.length > 0 && (
                      <TableHead>
                        <TableRow>
                          <TableCell>Development Stage</TableCell>
                          <TableCell>Environment</TableCell>
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
                                name="stage"
                                value={kvEnvs[idx].stage}
                                onChange={handleChange(idx, 'stage')}
                                variant="outlined"
                              />
                            </TableCell>
                            <TableCell>
                              <TextField
                                fullWidth
                                name="label"
                                value={kvEnvs[idx].label}
                                onChange={handleChange(idx, 'label')}
                                select
                                variant="outlined"
                              >
                                {environmentOps.map((environment) => (
                                  <MenuItem
                                    key={environment.environmentUri}
                                    value={environment.label}
                                  >
                                    {environment.label}
                                  </MenuItem>
                                ))}
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
                  <Box display="flex" justifyContent="flex-end" sx={{ p: 1 }}>
                    <LoadingButton
                      color="primary"
                      loading={isSubmitting}
                      onClick={() => UpdateEnvstoParent(kvEnvs)}
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
PipelineEnvironmentUpdateForm.propTypes = {
  environmentOptions: PropTypes.array.isRequired,
  UpdateEnvstoParent: PropTypes.func.isRequired
};
export default PipelineEnvironmentUpdateForm;
