import { CloudDownloadOutlined, CopyAllOutlined } from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import Autocomplete from '@mui/lab/Autocomplete';
import {
  Box,
  Breadcrumbs,
  Button,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Container,
  Divider,
  FormControlLabel,
  FormGroup,
  FormHelperText,
  Grid,
  IconButton,
  Link,
  Switch,
  TextField,
  Typography
} from '@mui/material';
import { useTheme } from '@mui/styles';

import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import React, { useCallback, useEffect, useState } from 'react';
import { CopyToClipboard } from 'react-copy-to-clipboard/lib/Component';
import { Helmet } from 'react-helmet-async';
import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom';
import * as Yup from 'yup';
import {
  createEnvironment,
  getPivotRoleExternalId,
  getPivotRoleName,
  getPivotRolePresignedUrl,
  getCDKExecPolicyPresignedUrl,
  getTrustAccount
} from '../services';
import {
  SanitizedHTML,
  ArrowLeftIcon,
  ChevronRightIcon,
  ChipInput,
  useSettings
} from 'design';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { getOrganization, useClient, useGroups } from 'services';
import {
  AwsRegions,
  isAnyEnvironmentModuleEnabled,
  isModuleEnabled,
  ModuleNames
} from 'utils';
import config from '../../../generated/config.json';

const EnvironmentCreateForm = (props) => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const params = useParams();
  const client = useClient();
  const groups = useGroups();
  const theme = useTheme();
  const { settings } = useSettings();
  const [organization, setOrganization] = useState({});
  const [trustedAccount, setTrustedAccount] = useState(null);
  const [pivotRoleName, setPivotRoleName] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchItem = useCallback(async () => {
    setLoading(true);
    const response = await client.query(getOrganization(params.uri));
    if (!response.errors) {
      setOrganization(response.data.getOrganization);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setLoading(false);
  }, [client, dispatch, params.uri]);
  const fetchTrustedAccount = useCallback(async () => {
    const response = await client.query(getTrustAccount(params.uri));
    if (!response.errors) {
      setTrustedAccount(response.data.getTrustAccount);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  }, [client, dispatch, params.uri]);
  const getRoleName = useCallback(async () => {
    const response = await client.query(getPivotRoleName(params.uri));
    if (!response.errors) {
      setPivotRoleName(response.data.getPivotRoleName);
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  }, [client, dispatch, params.uri]);
  const getPivotRoleUrl = async () => {
    const response = await client.query(getPivotRolePresignedUrl(params.uri));
    if (!response.errors) {
      window.open(response.data.getPivotRolePresignedUrl, '_blank');
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  const getCDKExecPolicyUrl = async () => {
    const response = await client.query(
      getCDKExecPolicyPresignedUrl(params.uri)
    );
    if (!response.errors) {
      window.open(response.data.getCDKExecPolicyPresignedUrl, '_blank');
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };

  const getExternalId = async () => {
    const response = await client.query(getPivotRoleExternalId(params.uri));
    if (!response.errors) {
      await navigator.clipboard.writeText(response.data.getPivotRoleExternalId);
      enqueueSnackbar('External Id copied to clipboard', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
  };
  const copyPivotRoleName = async () => {
    await navigator.clipboard.writeText(pivotRoleName);
    enqueueSnackbar('Pivot role name copied to clipboard', {
      anchorOrigin: {
        horizontal: 'right',
        vertical: 'top'
      },
      variant: 'success'
    });
  };
  const copyNotification = () => {
    enqueueSnackbar('Copied to clipboard', {
      anchorOrigin: {
        horizontal: 'right',
        vertical: 'top'
      },
      variant: 'success'
    });
  };
  useEffect(() => {
    if (client) {
      fetchTrustedAccount().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      getRoleName().catch((e) =>
        dispatch({ type: SET_ERROR, error: e.message })
      );
      fetchItem().catch((e) => dispatch({ type: SET_ERROR, error: e.message }));
    }
  }, [client, dispatch, fetchItem, fetchTrustedAccount, getRoleName]);

  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        createEnvironment({
          organizationUri: organization.organizationUri,
          AwsAccountId: values.AwsAccountId,
          label: values.label,
          SamlGroupName: values.SamlAdminGroupName,
          tags: values.tags,
          description: values.description,
          region: values.region,
          EnvironmentDefaultIAMRoleArn: values.EnvironmentDefaultIAMRoleArn,
          resourcePrefix: values.resourcePrefix,
          vpcId: values.vpcId,
          subnetIds: values.subnetIds,
          parameters: [
            {
              key: 'notebooksEnabled',
              value: String(values.notebooksEnabled)
            },
            {
              key: 'dashboardsEnabled',
              value: String(values.dashboardsEnabled)
            },
            {
              key: 'mlStudiosEnabled',
              value: String(values.mlStudiosEnabled)
            },
            {
              key: 'pipelinesEnabled',
              value: String(values.pipelinesEnabled)
            },
            {
              key: 'omicsEnabled',
              value: String(values.omicsEnabled)
            }
          ]
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Environment Created', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        navigate(
          `/console/environments/${response.data.createEnvironment.environmentUri}`
        );
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (err) {
      setStatus({ success: false });
      setErrors({ submit: err.message });
      setSubmitting(false);
      dispatch({ type: SET_ERROR, error: err.message });
    }
  }

  const regions = AwsRegions.map((region) => ({
    label: region.name,
    value: region.code
  }));

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <>
      <Helmet>
        <title>Environments: Environment Create | data.all</title>
      </Helmet>
      <Box
        sx={{
          backgroundColor: 'background.default',
          minHeight: '100%',
          py: 8
        }}
      >
        <Container maxWidth={settings.compact ? 'xl' : false}>
          <Grid container justifyContent="space-between" spacing={3}>
            <Grid item>
              <Typography color="textPrimary" variant="h5">
                Create a new environment
              </Typography>
              <Breadcrumbs
                aria-label="breadcrumb"
                separator={<ChevronRightIcon fontSize="small" />}
                sx={{ mt: 1 }}
              >
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to="/console/organizations"
                  variant="subtitle2"
                >
                  Organizations
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to={`/console/organizations/${organization.organizationUri}`}
                  variant="subtitle2"
                >
                  {organization.label}
                </Link>
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to={`/console/organizations/${organization.organizationUri}/link`}
                  variant="subtitle2"
                >
                  Link environment
                </Link>
              </Breadcrumbs>
            </Grid>
            <Grid item>
              <Box sx={{ m: -1 }}>
                <Button
                  color="primary"
                  component={RouterLink}
                  startIcon={<ArrowLeftIcon fontSize="small" />}
                  sx={{ mt: 1 }}
                  to={`/console/organizations/${organization.organizationUri}`}
                  variant="outlined"
                >
                  Cancel
                </Button>
              </Box>
            </Grid>
          </Grid>
          <Card sx={{ mt: 3 }}>
            <CardHeader title="Prerequisite Steps" />
            <Divider />
            <CardContent>
              {config.core.custom_env_linking_text !== undefined ? (
                <Box>
                  <Typography color="textSecondary" variant="subtitle2">
                    <SanitizedHTML
                      dirtyHTML={config.core.custom_env_linking_text}
                    />
                  </Typography>
                </Box>
              ) : (
                <>
                  <Box>
                    <Typography color="textSecondary" variant="subtitle2">
                      1. (OPTIONAL) As part of setting up your AWS Environment
                      with CDK you need to specify a IAM Policy that gives
                      permission for CDK to create AWS Resources via
                      CloudFormation (i.e. CDK Execution Policy). You optionally
                      can use the below CloudFormation template to create the
                      custom IAM policy that is more restrictive than the
                      default <b>AdministratorAccess</b> policy. To remove
                      permissions associated to the environment features -
                      Notebooks, MLStudio, Pipelines and Dashboards, please set
                      the respective parameters to <b>false</b> in the
                      CloudFormation template (default is true).
                    </Typography>
                    <Button
                      color="primary"
                      startIcon={<CloudDownloadOutlined fontSize="small" />}
                      sx={{ mt: 1, mb: 2, ml: 2 }}
                      variant="outlined"
                      onClick={() => {
                        getCDKExecPolicyUrl().catch((e) =>
                          dispatch({ type: SET_ERROR, error: e.message })
                        );
                      }}
                    >
                      CloudFormation stack for CDK custom execution policy
                    </Button>
                  </Box>
                  <Box>
                    <Typography color="textSecondary" variant="subtitle2">
                      2. Bootstrap your AWS account with AWS CDK
                    </Typography>
                    <Grid
                      container
                      rowSpacing={1}
                      columnSpacing={{ xs: 1, sm: 2, md: 3 }}
                    >
                      <Grid item xs={6}>
                        <Card>
                          <CardContent>
                            <Typography
                              sx={{ fontSize: 14 }}
                              color="text.secondary"
                              gutterBottom
                            >
                              If Using Default CDK Execution Policy:
                            </Typography>
                            <Typography color="textPrimary" variant="subtitle2">
                              <CopyToClipboard
                                onCopy={() => copyNotification()}
                                text={`cdk bootstrap --trust ${trustedAccount} -c @aws-cdk/core:newStyleStackSynthesis=true --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess aws://ACCOUNT_ID/REGION`}
                              >
                                <IconButton>
                                  <CopyAllOutlined
                                    sx={{
                                      color:
                                        theme.palette.mode === 'dark'
                                          ? theme.palette.primary.contrastText
                                          : theme.palette.primary.main
                                    }}
                                  />
                                </IconButton>
                              </CopyToClipboard>
                              {`cdk bootstrap --trust ${trustedAccount} -c @aws-cdk/core:newStyleStackSynthesis=true --cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess aws://ACCOUNT_ID/REGION`}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={6}>
                        <Card>
                          <CardContent>
                            <Typography
                              sx={{ fontSize: 14 }}
                              color="text.secondary"
                              gutterBottom
                            >
                              If Using Custom CDK Execution Policy (From Step
                              1):
                            </Typography>
                            <Typography color="textPrimary" variant="subtitle2">
                              <CopyToClipboard
                                onCopy={() => copyNotification()}
                                text={`aws cloudformation --region REGION create-stack --stack-name DataAllCustomCDKExecPolicyStack --template-body file://cdkExecPolicy.yaml --parameters ParameterKey=EnvironmentResourcePrefix,ParameterValue=dataall --capabilities CAPABILITY_NAMED_IAM && aws cloudformation wait stack-create-complete --stack-name DataAllCustomCDKExecPolicyStack --region REGION && cdk bootstrap --trust ${trustedAccount} -c @aws-cdk/core:newStyleStackSynthesis=true --cloudformation-execution-policies arn:aws:iam::ACCOUNT_ID:policy/DataAllCustomCDKPolicyREGION aws://ACCOUNT_ID/REGION`}
                              >
                                <IconButton>
                                  <CopyAllOutlined
                                    sx={{
                                      color:
                                        theme.palette.mode === 'dark'
                                          ? theme.palette.primary.contrastText
                                          : theme.palette.primary.main
                                    }}
                                  />
                                </IconButton>
                              </CopyToClipboard>
                              {`aws cloudformation --region REGION create-stack --stack-name DataAllCustomCDKExecPolicyStack --template-body file://cdkExecPolicy.yaml --parameters ParameterKey=EnvironmentResourcePrefix,ParameterValue=dataall --capabilities CAPABILITY_NAMED_IAM && aws cloudformation wait stack-create-complete --stack-name DataAllCustomCDKExecPolicyStack --region REGION && cdk bootstrap --trust ${trustedAccount} -c @aws-cdk/core:newStyleStackSynthesis=true --cloudformation-execution-policies arn:aws:iam::ACCOUNT_ID:policy/DataAllCustomCDKPolicyREGION aws://ACCOUNT_ID/REGION`}
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    </Grid>
                  </Box>
                  {process.env.REACT_APP_ENABLE_PIVOT_ROLE_AUTO_CREATE ===
                  'True' ? (
                    <Box>
                      <Typography color="textSecondary" variant="subtitle2">
                        3. As part of the environment CloudFormation stack
                        data.all will create an IAM role (Pivot Role) to manage
                        AWS operations in the environment AWS Account.
                      </Typography>
                    </Box>
                  ) : (
                    <Box>
                      <Box>
                        <Typography color="textSecondary" variant="subtitle2">
                          3. Create an IAM role named <b>{pivotRoleName}</b>{' '}
                          using the AWS CloudFormation stack below
                        </Typography>
                      </Box>
                      <Grid
                        container
                        justifyContent="space-between"
                        spacing={3}
                      >
                        <Grid item lg={6} xl={6} xs={6}>
                          <Button
                            color="primary"
                            startIcon={
                              <CloudDownloadOutlined fontSize="small" />
                            }
                            sx={{ mt: 1, mb: 2, ml: 2 }}
                            variant="outlined"
                            onClick={() => {
                              getPivotRoleUrl().catch((e) =>
                                dispatch({ type: SET_ERROR, error: e.message })
                              );
                            }}
                          >
                            CloudFormation stack
                          </Button>
                          <Button
                            color="primary"
                            startIcon={<CopyAllOutlined fontSize="small" />}
                            sx={{ mt: 1, mb: 2, ml: 2 }}
                            variant="outlined"
                            onClick={() => {
                              copyPivotRoleName().catch((e) =>
                                dispatch({ type: SET_ERROR, error: e.message })
                              );
                            }}
                          >
                            Pivot role name
                          </Button>
                          <Button
                            color="primary"
                            startIcon={<CopyAllOutlined fontSize="small" />}
                            sx={{ mt: 1, mb: 2, ml: 2 }}
                            variant="outlined"
                            onClick={() => {
                              getExternalId().catch((e) =>
                                dispatch({ type: SET_ERROR, error: e.message })
                              );
                            }}
                          >
                            External Id
                          </Button>
                        </Grid>
                      </Grid>
                    </Box>
                  )}
                  <Box>
                    <Typography color="textSecondary" variant="subtitle2">
                      Make sure that the services needed for the selected
                      environment features are available in your AWS Account.
                    </Typography>
                  </Box>
                </>
              )}
            </CardContent>
          </Card>
          <Box sx={{ mt: 3 }}>
            <Formik
              initialValues={{
                label: '',
                description: '',
                SamlAdminGroupName: '',
                AwsAccountId: '',
                region: '',
                tags: [],
                dashboardsEnabled: isModuleEnabled(ModuleNames.DASHBOARDS),
                notebooksEnabled: isModuleEnabled(ModuleNames.NOTEBOOKS),
                mlStudiosEnabled: isModuleEnabled(ModuleNames.MLSTUDIO),
                pipelinesEnabled: isModuleEnabled(ModuleNames.DATAPIPELINES),
                omicsEnabled: isModuleEnabled(ModuleNames.OMICS),
                EnvironmentDefaultIAMRoleArn: '',
                resourcePrefix: 'dataall',
                vpcId: '',
                subnetIds: []
              }}
              validationSchema={Yup.object().shape({
                label: Yup.string()
                  .max(255)
                  .required('*Environment name is required'),
                description: Yup.string().max(5000),
                SamlAdminGroupName: Yup.string()
                  .max(255)
                  .required('*Team is required'),
                AwsAccountId: Yup.number(
                  '*AWS account ID must be a number'
                ).required('*AWS account number is required'),
                region: Yup.string()
                  .required('*Region is required')
                  .test(
                    'region',
                    'Region is not supported',
                    (region) =>
                      regions.filter((option) =>
                        [option.label, option.value].includes(region)
                      ).length >= 1
                  ),
                tags: Yup.array().nullable(),
                subnetIds: Yup.array().when('vpcId', {
                  is: (value) => !!value,
                  then: Yup.array()
                    .min(1)
                    .required(
                      'At least 1 Subnet Id required if VPC Id specified'
                    )
                }),
                vpcId: Yup.string().nullable(),
                EnvironmentDefaultIAMRoleArn: Yup.string().nullable(),
                resourcePrefix: Yup.string()
                  .trim()
                  .matches(
                    '^[a-z-]*$',
                    '*Resource prefix is not valid (^[a-z-]*$)'
                  )
                  .min(1, '*Resource prefix must have at least 1 character')
                  .max(
                    20,
                    "*Resource prefix can't be longer than 20 characters"
                  )
                  .required('*Resource prefix is required')
              })}
              onSubmit={async (
                values,
                { setErrors, setStatus, setSubmitting }
              ) => {
                await submit(values, setStatus, setSubmitting, setErrors);
              }}
            >
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
                <form onSubmit={handleSubmit} {...props}>
                  <Grid container spacing={3}>
                    <Grid item lg={5} md={6} xs={12}>
                      <Card>
                        <CardHeader title="Details" />
                        <CardContent>
                          <TextField
                            error={Boolean(touched.label && errors.label)}
                            fullWidth
                            helperText={touched.label && errors.label}
                            label="Environment Name"
                            name="label"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.label}
                            variant="outlined"
                          />
                        </CardContent>
                        <CardContent>
                          <TextField
                            FormHelperTextProps={{
                              sx: {
                                textAlign: 'right',
                                mr: 0
                              }
                            }}
                            fullWidth
                            helperText={`${
                              200 - values.description.length
                            } characters left`}
                            label="Short description"
                            name="description"
                            multiline
                            onBlur={handleBlur}
                            onChange={handleChange}
                            rows={5}
                            value={values.description}
                            variant="outlined"
                          />
                          {touched.description && errors.description && (
                            <Box sx={{ mt: 2 }}>
                              <FormHelperText error>
                                {errors.description}
                              </FormHelperText>
                            </Box>
                          )}
                        </CardContent>
                        <CardContent>
                          <ChipInput
                            fullWidth
                            error={Boolean(touched.tags && errors.tags)}
                            helperText={touched.tags && errors.tags}
                            variant="outlined"
                            label="Tags"
                            placeholder="Hit enter after typing value"
                            onChange={(chip) => {
                              setFieldValue('tags', [...chip]);
                            }}
                          />
                        </CardContent>
                      </Card>
                      <Box sx={{ mt: 3 }}>
                        {isAnyEnvironmentModuleEnabled() && (
                          <Card>
                            <CardHeader title="Features management" />
                            <CardContent>
                              {isModuleEnabled(ModuleNames.DASHBOARDS) && (
                                <Box sx={{ ml: 2 }}>
                                  <FormGroup>
                                    <FormControlLabel
                                      color="primary"
                                      control={
                                        <Switch
                                          defaultChecked
                                          color="primary"
                                          onChange={handleChange}
                                          edge="start"
                                          name="dashboardsEnabled"
                                          value={values.dashboardsEnabled}
                                        />
                                      }
                                      label={
                                        <Typography
                                          color="textSecondary"
                                          gutterBottom
                                          variant="subtitle2"
                                        >
                                          Dashboards{' '}
                                          <small>
                                            (Requires Amazon QuickSight
                                            Enterprise Subscription)
                                          </small>
                                        </Typography>
                                      }
                                      labelPlacement="end"
                                      value={values.dashboardsEnabled}
                                    />
                                  </FormGroup>
                                </Box>
                              )}
                              {isModuleEnabled(ModuleNames.NOTEBOOKS) && (
                                <Box sx={{ ml: 2 }}>
                                  <FormGroup>
                                    <FormControlLabel
                                      color="primary"
                                      control={
                                        <Switch
                                          defaultChecked
                                          color="primary"
                                          onChange={handleChange}
                                          edge="start"
                                          name="notebooksEnabled"
                                          value={values.notebooksEnabled}
                                        />
                                      }
                                      label={
                                        <Box>
                                          <Typography
                                            color="textSecondary"
                                            gutterBottom
                                            variant="subtitle2"
                                          >
                                            Notebooks{' '}
                                            <small>
                                              (Requires Amazon Sagemaker
                                              notebook instances)
                                            </small>
                                          </Typography>
                                        </Box>
                                      }
                                      labelPlacement="end"
                                      value={values.notebooksEnabled}
                                    />
                                  </FormGroup>
                                </Box>
                              )}
                              {isModuleEnabled(ModuleNames.MLSTUDIO) && (
                                <Box sx={{ ml: 2 }}>
                                  <FormGroup>
                                    <FormControlLabel
                                      color="primary"
                                      control={
                                        <Switch
                                          defaultChecked
                                          color="primary"
                                          onChange={handleChange}
                                          edge="start"
                                          name="mlStudiosEnabled"
                                          value={values.mlStudiosEnabled}
                                        />
                                      }
                                      label={
                                        <Typography
                                          color="textSecondary"
                                          gutterBottom
                                          variant="subtitle2"
                                        >
                                          ML Studio{' '}
                                          <small>
                                            (Requires Amazon Sagemaker Studio)
                                          </small>
                                        </Typography>
                                      }
                                      labelPlacement="end"
                                    />
                                  </FormGroup>
                                </Box>
                              )}
                              {isModuleEnabled(ModuleNames.DATAPIPELINES) && (
                                <Box sx={{ ml: 2 }}>
                                  <FormGroup>
                                    <FormControlLabel
                                      color="primary"
                                      control={
                                        <Switch
                                          defaultChecked
                                          color="primary"
                                          onChange={handleChange}
                                          edge="start"
                                          name="pipelinesEnabled"
                                          value={values.pipelinesEnabled}
                                        />
                                      }
                                      label={
                                        <Typography
                                          color="textSecondary"
                                          gutterBottom
                                          variant="subtitle2"
                                        >
                                          Pipelines{' '}
                                          <small>(Requires AWS DevTools)</small>
                                        </Typography>
                                      }
                                      labelPlacement="end"
                                      value={values.pipelinesEnabled}
                                    />
                                  </FormGroup>
                                </Box>
                              )}
                              {isModuleEnabled(ModuleNames.OMICS) && (
                                <Box sx={{ ml: 2 }}>
                                  <FormGroup>
                                    <FormControlLabel
                                      color="primary"
                                      control={
                                        <Switch
                                          defaultChecked
                                          color="primary"
                                          onChange={handleChange}
                                          edge="start"
                                          name="omicsEnabled"
                                          value={values.omicsEnabled}
                                        />
                                      }
                                      label={
                                        <Typography
                                          color="textSecondary"
                                          gutterBottom
                                          variant="subtitle2"
                                        >
                                          Omics{' '}
                                          <small>
                                            (Requires AWS HealthOmics)
                                          </small>
                                        </Typography>
                                      }
                                      labelPlacement="end"
                                      value={values.omicsEnabled}
                                    />
                                  </FormGroup>
                                </Box>
                              )}
                            </CardContent>
                          </Card>
                        )}
                      </Box>
                    </Grid>
                    <Grid item lg={7} md={6} xs={12}>
                      <Box>
                        <Card>
                          <CardHeader title="Deployment" />
                          <CardContent>
                            <TextField
                              error={Boolean(
                                touched.AwsAccountId && errors.AwsAccountId
                              )}
                              fullWidth
                              helperText={
                                touched.AwsAccountId && errors.AwsAccountId
                              }
                              label="Account Number"
                              name="AwsAccountId"
                              onBlur={handleBlur}
                              onChange={handleChange}
                              value={values.AwsAccountId}
                              variant="outlined"
                            />
                          </CardContent>
                          <CardContent>
                            <Autocomplete
                              id="region"
                              freeSolo
                              options={regions.map((option) => option.label)}
                              onChange={(event, value) => {
                                const selectedRegion = regions.filter(
                                  (option) => option.label === value
                                );
                                setFieldValue(
                                  'region',
                                  selectedRegion
                                    ? selectedRegion[0].value
                                    : null
                                );
                              }}
                              renderInput={(regionParams) => (
                                <TextField
                                  {...regionParams}
                                  label="Region"
                                  margin="normal"
                                  error={Boolean(
                                    touched.region && errors.region
                                  )}
                                  helperText={touched.region && errors.region}
                                  onChange={handleChange}
                                  value={values.region}
                                  variant="outlined"
                                />
                              )}
                            />
                          </CardContent>
                          <CardContent>
                            <Autocomplete
                              id="SamlAdminGroupName"
                              disablePortal
                              options={groups}
                              onChange={(event, value) => {
                                if (value) {
                                  setFieldValue('SamlAdminGroupName', value);
                                } else {
                                  setFieldValue('SamlAdminGroupName', '');
                                }
                              }}
                              inputValue={values.SamlAdminGroupName}
                              renderInput={(params) => (
                                <TextField
                                  {...params}
                                  fullWidth
                                  error={Boolean(
                                    touched.SamlAdminGroupName &&
                                      errors.SamlAdminGroupName
                                  )}
                                  helperText={
                                    touched.SamlAdminGroupName &&
                                    errors.SamlAdminGroupName
                                  }
                                  label="Team"
                                  onChange={handleChange}
                                  name="SamlAdminGroupName"
                                  variant="outlined"
                                />
                              )}
                            />
                          </CardContent>
                          <CardContent>
                            <TextField
                              error={Boolean(
                                touched.resourcePrefix && errors.resourcePrefix
                              )}
                              fullWidth
                              helperText={
                                touched.resourcePrefix && errors.resourcePrefix
                              }
                              label="Resources Prefix"
                              placeholder="Prefix will be applied to All AWS resources created on this environment"
                              name="resourcePrefix"
                              onBlur={handleBlur}
                              onChange={handleChange}
                              value={values.resourcePrefix}
                              variant="outlined"
                            />
                          </CardContent>
                          <CardContent>
                            <TextField
                              error={Boolean(
                                touched.EnvironmentDefaultIAMRoleArn &&
                                  errors.EnvironmentDefaultIAMRoleArn
                              )}
                              fullWidth
                              helperText={
                                touched.EnvironmentDefaultIAMRoleArn &&
                                errors.EnvironmentDefaultIAMRoleArn
                              }
                              label="(Optional) IAM Role ARN"
                              placeholder="(Optional) Bring your own IAM role - Specify Entire Role ARN"
                              name="EnvironmentDefaultIAMRoleArn"
                              onBlur={handleBlur}
                              onChange={handleChange}
                              value={values.EnvironmentDefaultIAMRoleArn}
                              variant="outlined"
                            />
                          </CardContent>
                        </Card>
                      </Box>
                      {values.mlStudiosEnabled && (
                        <Box sx={{ mt: 3 }}>
                          <Card>
                            <CardHeader title="(Optional) ML Studio Configuration" />
                            <CardContent>
                              <TextField
                                {...params}
                                label="(Optional) ML Studio VPC ID"
                                placeholder="(Optional) Bring your own VPC - Specify VPC ID"
                                name="vpcId"
                                fullWidth
                                error={Boolean(touched.vpcId && errors.vpcId)}
                                helperText={touched.vpcId && errors.vpcId}
                                onBlur={handleBlur}
                                onChange={handleChange}
                                value={values.vpcId}
                                variant="outlined"
                              />
                            </CardContent>
                            <CardContent>
                              <ChipInput
                                fullWidth
                                error={Boolean(
                                  touched.subnetIds && errors.subnetIds
                                )}
                                helperText={
                                  touched.subnetIds && errors.subnetIds
                                }
                                variant="outlined"
                                label="(Optional) ML Studio Subnet ID(s)"
                                placeholder="(Optional) Bring your own VPC - Specify Subnet ID (Hit enter after typing value)"
                                onChange={(chip) => {
                                  setFieldValue('subnetIds', [...chip]);
                                }}
                              />
                            </CardContent>
                          </Card>
                        </Box>
                      )}
                      {errors.submit && (
                        <Box sx={{ mt: 3 }}>
                          <FormHelperText error>{errors.submit}</FormHelperText>
                        </Box>
                      )}
                      <Box
                        sx={{
                          display: 'flex',
                          justifyContent: 'flex-end',
                          mt: 3
                        }}
                      >
                        <LoadingButton
                          color="primary"
                          loading={isSubmitting}
                          type="submit"
                          variant="contained"
                        >
                          Create Environment
                        </LoadingButton>
                      </Box>
                    </Grid>
                  </Grid>
                </form>
              )}
            </Formik>
          </Box>
        </Container>
      </Box>
    </>
  );
};

export default EnvironmentCreateForm;
