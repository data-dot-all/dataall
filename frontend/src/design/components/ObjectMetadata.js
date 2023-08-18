import {
  Card,
  CardContent,
  CardHeader,
  Link,
  List,
  ListItem,
  Typography
} from '@mui/material';
import PropTypes from 'prop-types';
import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { StackStatus } from '.';
import { dayjs } from 'utils';
import { Label } from './Label';
import { TextAvatar } from './TextAvatar';

export const ObjectMetadata = (props) => {
  const {
    owner,
    admins,
    region,
    created,
    status,
    stewards,
    businessOwner,
    objectType,
    environment,
    organization,
    accountId,
    quicksightEnabled,
    ...other
  } = props;

  return (
    <Card {...other}>
      <CardHeader
        avatar={<TextAvatar name={owner} />}
        disableTypography
        subheader={
          <Link
            underline="hover"
            color="textPrimary"
            component={RouterLink}
            to="#"
            variant="subtitle2"
          >
            {owner}
          </Link>
        }
        style={{ paddingBottom: 0 }}
        title={
          <Typography color="textPrimary" display="block" variant="overline">
            Created by
          </Typography>
        }
      />
      <CardContent sx={{ pt: 0 }}>
        <List>
          {organization && (
            <ListItem
              disableGutters
              divider
              sx={{
                justifyContent: 'space-between',
                padding: 2
              }}
            >
              <Typography color="textSecondary" variant="subtitle2">
                Organization
              </Typography>
              <Typography color="textPrimary" variant="body2">
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to={`/console/organizations/${organization.organizationUri}`}
                  variant="subtitle2"
                >
                  {organization.label}
                </Link>
              </Typography>
            </ListItem>
          )}
          {environment && (
            <ListItem
              disableGutters
              divider
              sx={{
                justifyContent: 'space-between',
                padding: 2
              }}
            >
              <Typography color="textSecondary" variant="subtitle2">
                Environment
              </Typography>
              <Typography color="textPrimary" variant="body2">
                <Link
                  underline="hover"
                  color="textPrimary"
                  component={RouterLink}
                  to={`/console/environments/${environment.environmentUri}`}
                  variant="subtitle2"
                >
                  {environment.label}
                </Link>
              </Typography>
            </ListItem>
          )}
          {accountId && (
            <ListItem
              disableGutters
              divider
              sx={{
                justifyContent: 'space-between',
                padding: 2
              }}
            >
              <Typography color="textSecondary" variant="subtitle2">
                AWS account
              </Typography>
              <Typography color="textPrimary" variant="body2">
                {accountId}
              </Typography>
            </ListItem>
          )}
          {region && (
            <ListItem
              disableGutters
              divider
              sx={{
                justifyContent: 'space-between',
                padding: 2
              }}
            >
              <Typography color="textSecondary" variant="subtitle2">
                Region
              </Typography>
              <Typography color="textPrimary" variant="body2">
                {region}
              </Typography>
            </ListItem>
          )}

          {admins && (
            <ListItem
              disableGutters
              divider
              sx={{
                justifyContent: 'space-between',
                padding: 2
              }}
            >
              <Typography color="textSecondary" variant="subtitle2">
                Team
              </Typography>
              <Typography color="textPrimary" variant="body2">
                {admins}
              </Typography>
            </ListItem>
          )}
          {quicksightEnabled && (
            <ListItem
              disableGutters
              divider
              sx={{
                justifyContent: 'space-between',
                padding: 2
              }}
            >
              <Typography color="textSecondary" variant="subtitle2">
                QuickSight integration
              </Typography>
              <Typography color="textPrimary" variant="body2">
                <Label color="info">{quicksightEnabled ? 'Yes' : 'No'}</Label>
              </Typography>
            </ListItem>
          )}
          {objectType && objectType === 'dataset' && stewards && (
            <ListItem
              disableGutters
              divider
              sx={{
                justifyContent: 'space-between',
                padding: 2
              }}
            >
              <Typography color="textSecondary" variant="subtitle2">
                Stewards
              </Typography>
              <Typography color="textPrimary" variant="body2">
                {stewards || '-'}
              </Typography>
            </ListItem>
          )}

          <ListItem
            disableGutters
            divider
            sx={{
              justifyContent: 'space-between',
              padding: 2
            }}
          >
            <Typography color="textSecondary" variant="subtitle2">
              Created
            </Typography>
            <Typography color="textPrimary" variant="body2">
              {dayjs(created).fromNow()}
            </Typography>
          </ListItem>
          {status && (
            <ListItem
              disableGutters
              sx={{
                justifyContent: 'space-between',
                padding: 2
              }}
            >
              <Typography color="textSecondary" variant="subtitle2">
                Status
              </Typography>
              <Typography color="textPrimary" variant="body2">
                <StackStatus status={status} />
              </Typography>
            </ListItem>
          )}
        </List>
      </CardContent>
    </Card>
  );
};

ObjectMetadata.propTypes = {
  environment: PropTypes.string,
  accountId: PropTypes.string,
  organization: PropTypes.string,
  region: PropTypes.string,
  owner: PropTypes.string,
  admins: PropTypes.string,
  created: PropTypes.string,
  status: PropTypes.string,
  stewards: PropTypes.array,
  businessOwner: PropTypes.string,
  objectType: PropTypes.string,
  quicksightEnabled: PropTypes.bool
};
