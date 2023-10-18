// TODO: completely
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
import * as FiIcons from 'react-icons/fi';
import { Link as RouterLink } from 'react-router-dom';
import PropTypes from 'prop-types';
import { useNavigate } from 'react-router';
import { FiCodesandbox } from 'react-icons/fi';
import React from 'react';

import { IconAvatar, StackStatus, useCardStyle } from 'design';

export const OmicsWorkflowsListItem = (props) => {
  const { workflow } = props;
  const classes = useCardStyle();
  const navigate = useNavigate();
  return (
    <Grid item key={workflow.id} md={3} xs={12} {...props}>
      <Card key={workflow.id} className={classes.card} raised>
        <Box sx={{ p: 2 }}>
          <Box
            sx={{
              alignItems: 'left',
              display: 'flex'
            }}
          >
            <IconAvatar icon={<FiCodesandbox size={18} />} />
            <Box sx={{ ml: 2 }}>
              <Link
                underline="hover"
                component="button"
                color="textPrimary"
                variant="h6"
                onClick={() => {
                  navigate(`/console/omics/workflows/${workflow.id}`);
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
                <Tooltip title={workflow.id}>
                  <span>Workflow id: {workflow.id}</span>
                </Tooltip>
              </Link>
              <Typography color="textSecondary" variant="body2">
                <Link underline="hover" color="textPrimary" variant="subtitle2">
                  {workflow.name}
                </Link>
              </Typography>
            </Box>
          </Box>
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
                <FiIcons.FiActivity /> Type
              </Typography>
            </Grid>
            <Grid item md={8} xs={12}>
              <Typography color="textPrimary" variant="body2">
                {workflow.type}
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
                <StackStatus status={workflow.status} />
              </Typography>
            </Grid>
          </Grid>
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
            key={workflow.id}
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
              to={`/console/omics/workflows/${workflow.id}`}
            >
              Learn More
            </Button>
          </Box>
        </Box>
      </Card>
    </Grid>
  );
};
OmicsWorkflowsListItem.propTypes = {
  workflow: PropTypes.object.isRequired
};
