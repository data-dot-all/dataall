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
import { AiOutlineExperiment } from 'react-icons/ai';
import * as FaIcons from 'react-icons/fa';
import { useNavigate } from 'react-router';
import { Link as RouterLink } from 'react-router-dom';
import { IconAvatar, Label, useCardStyle } from 'design';

export const WorksheetListItem = (props) => {
  const { worksheet } = props;
  const classes = useCardStyle();
  const navigate = useNavigate();
  return (
    <Grid item key={worksheet.worksheetUri} md={3} xs={12} {...props}>
      <Card key={worksheet.worksheetUri} className={classes.card} raised>
        <Box sx={{ p: 2 }}>
          <Box
            sx={{
              alignItems: 'center',
              display: 'flex'
            }}
          >
            <IconAvatar icon={<AiOutlineExperiment size={20} />} />
            <Box sx={{ ml: 1 }}>
              <Link
                underline="hover"
                component="button"
                color="textPrimary"
                variant="h6"
                onClick={() => {
                  navigate(`/console/worksheets/${worksheet.worksheetUri}`);
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
                <Tooltip title={worksheet.label}>
                  <span>{worksheet.label}</span>
                </Tooltip>
              </Link>
              <Typography color="textSecondary" variant="body2">
                by{' '}
                <Link underline="hover" color="textPrimary" variant="subtitle2">
                  {worksheet.owner}
                </Link>
              </Typography>
            </Box>
          </Box>
        </Box>
        <Box
          sx={{
            pb: 2,
            px: 3
          }}
        >
          <Typography
            color="textSecondary"
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
            <Tooltip title={worksheet.description || 'No description provided'}>
              <span>{worksheet.description || 'No description provided'}</span>
            </Tooltip>
          </Typography>
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
                <FaIcons.FaUserShield /> Role
              </Typography>
            </Grid>
            <Grid item md={8} xs={12}>
              <Label
                color={
                  worksheet.userRoleForWorksheet === 'Creator'
                    ? 'primary'
                    : 'info'
                }
              >
                {worksheet.userRoleForWorksheet || '-'}
              </Label>
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
                <Tooltip title={worksheet.SamlAdminGroupName || '-'}>
                  <span>{worksheet.SamlAdminGroupName || '-'}</span>
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
        />
        <Box
          sx={{
            px: 3,
            py: 1
          }}
        >
          <Grid
            alignItems="center"
            container
            key={worksheet.worksheetUri}
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
              to={`/console/worksheets/${worksheet.worksheetUri}`}
            >
              Learn More
            </Button>
          </Box>
        </Box>
      </Card>
    </Grid>
  );
};
WorksheetListItem.propTypes = {
  worksheet: PropTypes.object.isRequired
};
