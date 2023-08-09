import {
  CopyAllOutlined,
  NotificationsActive,
  NotificationsOff
} from '@mui/icons-material';
import { LoadingButton } from '@mui/lab';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Dialog,
  Divider,
  FormHelperText,
  IconButton,
  Switch,
  TextField,
  Typography
} from '@mui/material';
import { useTheme } from '@mui/styles';
import { Formik } from 'formik';
import { useSnackbar } from 'notistack';
import PropTypes from 'prop-types';
import React, { useState } from 'react';
import { CopyToClipboard } from 'react-copy-to-clipboard/lib/Component';
import * as Yup from 'yup';
import { SET_ERROR, useDispatch } from 'globalErrors';
import { useClient } from 'services';
import { disableDataSubscriptions, enableDataSubscriptions } from '../services';

export const EnvironmentSubscriptions = ({ environment, fetchItem }) => {
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  const client = useClient();
  const theme = useTheme();
  const [disabling, setDisabling] = useState(false);
  const [isEnableSubscriptionsModalOpen, setIsEnableSubscriptionsModalOpen] =
    useState(false);
  const handleEnableSubscriptionsModalOpen = () => {
    setIsEnableSubscriptionsModalOpen(true);
  };

  const handleEnableSubscriptionsModalClose = () => {
    setIsEnableSubscriptionsModalOpen(false);
  };

  const disableSubscriptions = async () => {
    setDisabling(true);
    const response = await client.mutate(
      disableDataSubscriptions({
        environmentUri: environment.environmentUri
      })
    );
    if (!response.errors) {
      fetchItem();
      enqueueSnackbar('Subscriptions disabled', {
        anchorOrigin: {
          horizontal: 'right',
          vertical: 'top'
        },
        variant: 'success'
      });
    } else {
      dispatch({ type: SET_ERROR, error: response.errors[0].message });
    }
    setDisabling(false);
  };
  async function submit(values, setStatus, setSubmitting, setErrors) {
    try {
      const response = await client.mutate(
        enableDataSubscriptions({
          environmentUri: environment.environmentUri,
          input: {
            producersTopicArn: values.topic
          }
        })
      );
      if (!response.errors) {
        setStatus({ success: true });
        setSubmitting(false);
        enqueueSnackbar('Subscriptions enabled', {
          anchorOrigin: {
            horizontal: 'right',
            vertical: 'top'
          },
          variant: 'success'
        });
        handleEnableSubscriptionsModalClose();
        fetchItem();
      } else {
        dispatch({ type: SET_ERROR, error: response.errors[0].message });
      }
    } catch (err) {
      console.error(err);
      setStatus({ success: false });
      setErrors({ submit: err.message });
      setSubmitting(false);
      dispatch({ type: SET_ERROR, error: err.message });
    }
  }
  return (
    <Box>
      <Box display="flex" justifyContent="flex-end" sx={{ p: 1 }}>
        {environment.subscriptionsEnabled && (
          <LoadingButton
            color="primary"
            loading={disabling}
            onClick={disableSubscriptions}
            startIcon={<NotificationsOff fontSize="small" />}
            sx={{ m: 1 }}
            variant="outlined"
          >
            Disable Subscriptions
          </LoadingButton>
        )}
        {!environment.subscriptionsEnabled && (
          <Button
            color="primary"
            onClick={handleEnableSubscriptionsModalOpen}
            startIcon={<NotificationsActive fontSize="small" />}
            sx={{ m: 1 }}
            variant="outlined"
          >
            Enable Subscriptions
          </Button>
        )}
      </Box>
      {environment.subscriptionsEnabled && (
        <Box>
          <Card>
            <CardHeader
              title="Data Producers Topic"
              subheader={
                <Typography color="textSecondary" variant="subtitle2">
                  Subscribe your data processes to SNS topic and publish the
                  latest datasets updates to data consumers.
                </Typography>
              }
            />
            <Divider />
            <CardContent>
              <Box>
                <Typography color="textSecondary" variant="subtitle2">
                  Topic Arn
                </Typography>
                <Typography color="textPrimary" variant="subtitle2">
                  <CopyToClipboard
                    onCopy={() => {}}
                    text={`arn:aws:sns:${environment.region}:${environment.AwsAccountId}:${environment.subscriptionsProducersTopicName}`}
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
                  {`arn:aws:sns:${environment.region}:${environment.AwsAccountId}:${environment.subscriptionsProducersTopicName}`}
                </Typography>
              </Box>
            </CardContent>
          </Card>
          <Card sx={{ mt: 3 }}>
            <CardHeader
              title="Data Consumers Topic"
              subheader={
                <Typography color="textSecondary" variant="subtitle2">
                  Subscribe your data processes to SNS topic and receive the
                  latest datasets updates from data owners.
                </Typography>
              }
            />
            <Divider />
            <CardContent>
              <Box>
                <Typography color="textSecondary" variant="subtitle2">
                  Topic Arn
                </Typography>
                <Typography color="textPrimary" variant="subtitle2">
                  <CopyToClipboard
                    onCopy={() => {}}
                    text={`arn:aws:sns:${environment.region}:${environment.AwsAccountId}:${environment.subscriptionsConsumersTopicName}`}
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
                  {`arn:aws:sns:${environment.region}:${environment.AwsAccountId}:${environment.subscriptionsConsumersTopicName}`}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Box>
      )}
      {isEnableSubscriptionsModalOpen && (
        <Dialog
          maxWidth="md"
          fullWidth
          onClose={handleEnableSubscriptionsModalClose}
          open={handleEnableSubscriptionsModalOpen}
        >
          <Box sx={{ p: 3 }}>
            <Typography
              align="center"
              color="textPrimary"
              gutterBottom
              variant="h4"
            >
              Enable Subscriptions
            </Typography>
            <Typography
              align="center"
              color="textSecondary"
              variant="subtitle2"
            >
              <p>
                Bring your own topic by assigning your SNS topic&apos;s name or
                a new one will be created for your environment.
              </p>
            </Typography>
            <Box sx={{ p: 3 }}>
              <Formik
                initialValues={{
                  topicEnabled: false,
                  topic: ''
                }}
                validationSchema={Yup.object().shape({
                  topic: Yup.string().when('topicEnabled', {
                    is: true,
                    then: Yup.string().required('Topic name is required')
                  })
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
                  touched,
                  values
                }) => (
                  <form onSubmit={handleSubmit}>
                    <Box>
                      <CardContent>
                        <Typography
                          color="textSecondary"
                          gutterBottom
                          variant="subtitle2"
                        >
                          Bring your own topic
                        </Typography>
                        <Switch
                          color="primary"
                          onChange={handleChange}
                          edge="start"
                          name="topicEnabled"
                          value={values.topicEnabled}
                        />
                      </CardContent>
                      {values.topicEnabled && (
                        <CardContent>
                          <TextField
                            error={Boolean(touched.topic && errors.topic)}
                            fullWidth
                            helperText={touched.topic && errors.topic}
                            label="Topic name"
                            name="topic"
                            onBlur={handleBlur}
                            onChange={handleChange}
                            value={values.topic}
                            variant="outlined"
                          />
                        </CardContent>
                      )}
                    </Box>
                    {errors.submit && (
                      <Box sx={{ mt: 3 }}>
                        <FormHelperText error>{errors.submit}</FormHelperText>
                      </Box>
                    )}
                    <CardContent>
                      <LoadingButton
                        fullWidth
                        startIcon={<NotificationsActive size={15} />}
                        color="primary"
                        disabled={isSubmitting}
                        type="submit"
                        variant="contained"
                      >
                        Enable Subscriptions
                      </LoadingButton>
                    </CardContent>
                  </form>
                )}
              </Formik>
            </Box>
          </Box>
        </Dialog>
      )}
    </Box>
  );
};

EnvironmentSubscriptions.propTypes = {
  environment: PropTypes.object.isRequired,
  fetchItem: PropTypes.func.isRequired
};
