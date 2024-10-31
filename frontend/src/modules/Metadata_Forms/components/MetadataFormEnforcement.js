import PropTypes from 'prop-types';
import {
  Autocomplete,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader, Checkbox,
  Dialog, FormControlLabel,
  Grid,
  TextField,
  Typography
} from '@mui/material';
import { PlusIcon } from 'design';
import React, { useEffect, useState } from 'react';
import DeleteIcon from '@mui/icons-material/DeleteOutlined';
import DoNotDisturbAltOutlinedIcon from '@mui/icons-material/DoNotDisturbAltOutlined';
import { fetchEnums, useClient } from 'services';
import { useDispatch } from 'react-redux';
import { SET_ERROR } from 'globalErrors';
import { createMetadataFormEnforcementRule, listMetadataFormEnforcementRules } from '../services';
import * as Yup from 'yup';
import { Formik } from 'formik';
import FormControl from '@mui/material/FormControl';
import { LoadingButton } from '@mui/lab';
import SendIcon from '@mui/icons-material/Send';


const CreateEnforcementRuleModal = (props) => {
  const { onClose, open, metadataForm,severityOptions,entityTypesOptions,enforcementScopeOptions, ...other } = props;

  const client = useClient();

  const enforcementScopeDict = {}
  for (const option of enforcementScopeOptions) {
    enforcementScopeDict[option.name] = option.value;
  }

  async function submit(values, setStatus, setSubmitting, setErrors) {
    const input = {
      metadataFormUri: metadataForm.uri,
      version: values.version,
      level: values.scope,
      severity: values.severity,
      homeEntity: '9hj226qv',
      entityTypes: values.entityTypes
    }
    const response = await client.mutate(createMetadataFormEnforcementRule(input));
    if (response.errors) {
      setStatus({ success: false });
      setErrors({ submit: response.errors[0].message });
      setSubmitting(false);
    } else {
      setStatus({ success: true });
      setSubmitting(false);
      props.refetch();
      onClose();
    }
  }

  return (
    <Dialog maxWidth="md" fullWidth onClose={onClose} open={open} {...other}>
      <Box sx={{ p: 3 }}>
        <Typography
          align="center"
          color="textPrimary"
          gutterBottom
          variant="h4"
        >
          Enforce {metadataForm.name}
        </Typography>
        <Formik
         initialValues={{
           version: metadataForm.versions[0],
           scope: enforcementScopeDict['Global'],
           severity: severityOptions[0].value,
           entityTypes: []

         }} onSubmit={async (values, { setErrors, setStatus, setSubmitting }) => {
          await submit(values, setStatus, setSubmitting, setErrors);
        }}>
          {({
              errors,
              handleBlur,
              handleChange,
              handleSubmit,
              isSubmitting,
              setFieldValue,
              touched,
              values
            }) => (
            <form onSubmit={handleSubmit}>
              <Box>
                <CardContent>
                  <Autocomplete
                    id="version"
                    disablePortal
                    options={metadataForm.versions.map((option) => {
                      return {
                        label: 'version ' + option,
                        value: option
                      };
                    })}
                    onChange={(event, value) => {
                      setFieldValue('version', value.value);
                    }}
                    defaultValue={'version ' + metadataForm.versions[0]}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        fullWidth
                        error={Boolean(touched.version && errors.version)}
                        helperText={touched.version && errors.version}
                        label="Version"
                        onChange={handleChange}
                        variant="outlined"
                      />
                    )}
                  />
                </CardContent>
                <CardContent>
                  <Autocomplete
                    id="scope"
                    disablePortal
                    options={enforcementScopeOptions.map((option) => {
                      return {
                        label: option.name,
                        value: option.value,
                      };
                    })}
                    defaultValue={enforcementScopeDict['Global']}
                    onChange={(event, value) => {
                      setFieldValue('scope', value.value);
                    }}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        fullWidth
                        error={Boolean(touched.scope && errors.scope)}
                        helperText={touched.scope && errors.scope}
                        label="Enforcement Level"
                        onChange={handleChange}
                        variant="outlined"
                      />
                    )}
                  />
                </CardContent>
                <CardContent>
                  <Autocomplete
                    id="severity"
                    disablePortal
                    options={severityOptions.map((option) => {
                      return {
                        label: option.name,
                        value: option.value
                      };
                    })}
                    onChange={(event, value) => {
                      setFieldValue('severity', value.value);
                    }}
                    defaultValue={severityOptions[0].value}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        fullWidth
                        error={Boolean(touched.severity && errors.severity)}
                        helperText={touched.severity && errors.severity}
                        label="Severity"
                        onChange={handleChange}
                        variant="outlined"
                      />
                    )}
                  />
                </CardContent>
                <CardContent>
                  <Grid
                    container
                    spacing={2}
                  >

                {entityTypesOptions.map((entityType) => (
                  <Grid item lg={4} xl={4}>
                    <FormControlLabel control={<Checkbox id={entityType.name}  onChange={(event, value) => {
                      if(value){

                        setFieldValue('entityTypes', [...values.entityTypes, entityType.value]);
                      }
                      else{
                        setFieldValue('entityTypes', values.entityTypes.filter((item) => item !== entityType.value));
                      }
                    }}/>} label={entityType.value} />
                  </Grid>
                ))}
                  </Grid>
              </CardContent>
                <CardContent>
                  <LoadingButton
                    fullWidth
                    startIcon={<SendIcon fontSize="small" />}
                    color="primary"
                    disabled={isSubmitting}
                    type="submit"
                    variant="contained"
                  >
                    Create
                  </LoadingButton>

                  <Button
                    sx={{ mt: 2 }}
                    onClick={onClose}
                    fullWidth
                    color="primary"
                    variant="outlined"
                    disabled={isSubmitting}
                  >
                    Cancel
                  </Button>
                </CardContent>
              </Box>
            </form>
          )}
        </Formik>
      </Box>
    </Dialog>
  );
};

export const MetadataFormEnforcement = (props) => {
  const {canEdit, metadataForm} = props;
  const client = useClient();
  const dispatch = useDispatch();
  const [showCreateRuleModal, setShowCreateRuleModal] = useState(false);
  const [rules, setRules] = useState([]);
  const [severityOptions, setSeverityOptions] = useState({});
  const [entityTypesOptions, setEntityTypesOptions] = useState({})
  const [enforcementScopeOptions, setEnforcementScopeOptions] = useState({})


  const fetchEnforcementRules = async () => {
    const response =  await client.query(listMetadataFormEnforcementRules(metadataForm.uri));
    if (!response.errors && response.data && response.data.listMetadataFormEnforcementRules) {
      setRules(response.data.listMetadataFormEnforcementRules);
    }
  };

  const fetchEnforcementEnums = async () => {
    const enums = await fetchEnums(client, [
      'MetadataFormEntityTypes',
      'MetadataFormEnforcementSeverity',
      'MetadataFormEnforcementScope'
    ]);
    if (enums['MetadataFormEntityTypes'].length > 0) {
      setEntityTypesOptions(enums['MetadataFormEntityTypes']);
    } else {
      const error = 'Could not fetch entity type options';
      dispatch({ type: SET_ERROR, error });
    }
    if (enums['MetadataFormEnforcementSeverity'].length > 0) {
      setSeverityOptions(enums['MetadataFormEnforcementSeverity']);
    } else {
      const error = 'Could not fetch enforcement severity options';
      dispatch({ type: SET_ERROR, error });
    }
    if (enums['MetadataFormEnforcementScope'].length > 0) {
      setEnforcementScopeOptions(enums['MetadataFormEnforcementScope']);
    } else {
      const error = 'Could not fetch enforcement scope options';
      dispatch({ type: SET_ERROR, error });
    }
  };

  useEffect(() => {
    if (client) {
      fetchEnforcementRules().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
      fetchEnforcementEnums().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client]);

  return (
    <Box>
      <Grid
        container
        spacing={2}
        sx={{ height: 'calc(100vh - 320px)', mb: -5 }}
      >
        <Grid item lg={5} xl={5}>
          <Card sx={{ height: '100%' }}>
            <Grid
              container
              spacing={2}
            >
              <Grid item lg={8} xl={8}>
                <CardHeader title = 'Enforcement rules'></CardHeader>
              </Grid>
              <Grid item lg={4} xl={4}  sx={{
                textAlign: 'right'
              }}>
                {canEdit && (
                    <CardContent>
                      <Button
                        color="primary"
                        startIcon={<PlusIcon size={15} />}
                        type="button"
                        onClick={() => setShowCreateRuleModal(true)}
                      >
                        Add rule
                      </Button>
                    </CardContent>
                )}
              </Grid>
            </Grid>
            {rules.length > 0 ? (
              rules.map((rule) => (
                <CardContent>
                  <Typography variant="subtitle2" color="textPrimary">
                    rule.uri
                  </Typography>
                </CardContent>
              ))
            ) : (
              <CardContent sx={{ display: 'flex', justifyContent: 'center' }}>
                <DoNotDisturbAltOutlinedIcon sx={{ mr: 1 }} />
                <Typography variant="subtitle2" color="textPrimary">
                  Metadata Form is not enforced
                </Typography>
              </CardContent>
            )}
          </Card>
        </Grid>
      </Grid>
      {showCreateRuleModal && (
        <CreateEnforcementRuleModal
          open={showCreateRuleModal}
          metadataForm={metadataForm}
          enforcementScopeOptions={enforcementScopeOptions}
          entityTypesOptions={entityTypesOptions}
          severityOptions={severityOptions}
          onClose={() => setShowCreateRuleModal(false)}
        />
      )}
    </Box>
  );
};

MetadataFormEnforcement.propTypes = {
  metadataForm: PropTypes.any.isRequired
};
