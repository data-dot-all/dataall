import {
  Box,
  Button,
  Card,
  Divider,
  Grid,
  Link,
  Tooltip,
  Typography
} from '@mui/material';
import PropTypes from 'prop-types';
import React from 'react';
import * as FaIcons from 'react-icons/fa';
import * as FiIcons from 'react-icons/fi';
import { SiJupyter } from 'react-icons/si';
import { useNavigate } from 'react-router';
import { Link as RouterLink } from 'react-router-dom';
import { IconAvatar, Label, StackStatus, useCardStyle } from 'design';

/**
 * @description NotebookListItem view.
 * @param {Object} props
 * @return {JSX.Element}
 */
export const NotebookListItem = (props) => {
  const { notebook } = props;
  const classes = useCardStyle();
  const navigate = useNavigate();

  return (
    <Grid item key={notebook.notebookUri} md={3} xs={12} {...props}>
      <Card key={notebook.notebookUri} className={classes.card} raised>
        <Box sx={{ p: 2 }}>
          <Box
            sx={{
              alignItems: 'center',
              display: 'flex'
            }}
          >
            <IconAvatar icon={<SiJupyter size={20} />} />
            <Box sx={{ ml: 2 }}>
              <Link
                underline="hover"
                component="button"
                color="textPrimary"
                variant="h6"
                onClick={() => {
                  navigate(`/console/notebooks/${notebook.notebookUri}`);
                }}
                sx={{
                  width: '99%',
                  whiteSpace: 'nowrap',
                  alignItems: 'left',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  WebkitBoxOrient: 'vertical',
                  WebkitLineClamp: 2
                }}
              >
                <Tooltip title={notebook.label}>
                  <span>{notebook.label}</span>
                </Tooltip>
              </Link>
              <Typography color="textSecondary" variant="body2">
                by{' '}
                <Link underline="hover" color="textPrimary" variant="subtitle2">
                  {notebook.owner}
                </Link>
              </Typography>
            </Box>
          </Box>
        </Box>
        <Box>
          <Box
            sx={{
              px: 3,
              py: 0.5
            }}
          >
            <Grid container>
              <Grid item md={4} xs={12}>
                <Typography color="textSecondary" variant="body2">
                  <FaIcons.FaUserShield /> Role
                </Typography>
              </Grid>
              <Grid item md={8} xs={12}>
                <Typography color="textPrimary" variant="body2">
                  <Label
                    color={
                      notebook.userRoleForNotebook === 'Creator'
                        ? 'primary'
                        : 'info'
                    }
                  >
                    {notebook.userRoleForNotebook || '-'}
                  </Label>
                </Typography>
              </Grid>
            </Grid>
          </Box>
          <Box
            sx={{
              px: 3,
              py: 0.5
            }}
          >
            <Grid container>
              <Grid item md={4} xs={12}>
                <Typography color="textSecondary" variant="body2">
                  <FaIcons.FaUsersCog /> Team
                </Typography>
              </Grid>
              <Grid item md={8} xs={12}>
                <Typography
                  color="textPrimary"
                  variant="body2"
                  sx={{
                    width: '200px',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    WebkitBoxOrient: 'vertical',
                    WebkitLineClamp: 2
                  }}
                >
                  <Tooltip title={notebook.SamlAdminGroupName || '-'}>
                    <span>{notebook.SamlAdminGroupName || '-'}</span>
                  </Tooltip>
                </Typography>
              </Grid>
            </Grid>
          </Box>
          <Box
            sx={{
              px: 3,
              py: 0.5
            }}
          >
            <Grid container>
              <Grid item md={4} xs={12}>
                <Typography color="textSecondary" variant="body2">
                  <FaIcons.FaAws /> Account
                </Typography>
              </Grid>
              <Grid item md={8} xs={6}>
                <Typography color="textPrimary" variant="body2">
                  {notebook.environment.AwsAccountId}
                </Typography>
              </Grid>
            </Grid>
          </Box>
          <Box
            sx={{
              px: 3,
              py: 0.5
            }}
          >
            <Grid container>
              <Grid item md={4} xs={12}>
                <Typography color="textSecondary" variant="body2">
                  <FaIcons.FaGlobe /> Region
                </Typography>
              </Grid>
              <Grid item md={8} xs={12}>
                <Typography color="textPrimary" variant="body2">
                  {notebook.environment.region}
                </Typography>
              </Grid>
            </Grid>
          </Box>
          <Box
            sx={{
              px: 3,
              py: 0.5
            }}
          >
            <Grid container>
              <Grid item md={4} xs={12}>
                <Typography color="textSecondary" variant="body2">
                  <FiIcons.FiActivity /> Status
                </Typography>
              </Grid>
              <Grid item md={8} xs={12}>
                <Typography color="textPrimary" variant="body2">
                  <StackStatus status={notebook.stack.status} />
                </Typography>
              </Grid>
            </Grid>
          </Box>
        </Box>
        <Box
          sx={{
            px: 3,
            py: 1
          }}
        >
          <Grid
            alignItems="center"
            container
            key={notebook.notebookUri}
            justifyContent="space-between"
            spacing={3}
          />
        </Box>
        <Divider />
        <Box
          sx={{
            alignItems: 'center',
            display: 'flex',
            pl: 1,
            pr: 3,
            py: 0.5
          }}
        >
          <Box
            sx={{
              alignItems: 'center',
              display: 'flex'
            }}
          >
            <Button
              color="primary"
              component={RouterLink}
              to={`/console/notebooks/${notebook.notebookUri}`}
            >
              Learn More
            </Button>
          </Box>
        </Box>
      </Card>
    </Grid>
  );
};

NotebookListItem.propTypes = {
  notebook: PropTypes.object.isRequired
};
