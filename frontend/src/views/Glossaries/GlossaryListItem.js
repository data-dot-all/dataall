import { Box, Button, Card, Divider, Grid, Link, Tooltip, Typography } from '@material-ui/core';
import { Link as RouterLink } from 'react-router-dom';
import PropTypes from 'prop-types';
import { useNavigate } from 'react-router';
import { BsBookmark, BsTag } from 'react-icons/bs';
import React from 'react';
import * as FaIcons from 'react-icons/fa';
import IconAvatar from '../../components/IconAvatar';
import useCardStyle from '../../hooks/useCardStyle';

const GlossaryListItem = (props) => {
  const { glossary } = props;
  const classes = useCardStyle();
  const navigate = useNavigate();
  return (
    <Grid
      item
      key={glossary.nodeUri}
      md={3}
      xs={12}
      {...props}
    >
      <Card
        key={glossary.nodeUri}
        className={classes.card}
        raised
      >
        <Box sx={{ p: 2 }}>
          <Box
            sx={{
              alignItems: 'center',
              display: 'flex'
            }}
          >
            <IconAvatar icon={<BsTag size={15} />} />
            <Box sx={{ ml: 2 }}>
              <Link
                component="button"
                color="textPrimary"
                variant="h6"
                onClick={() => {
                  navigate(`/console/glossaries/${glossary.nodeUri}`);
                }}
                sx={{
                  width: '99%',
                  float: 'left',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  WebkitBoxOrient: 'vertical',
                  WebkitLineClamp: 2
                }}
              >
                <Tooltip title={glossary.label}><span>{glossary.label}</span></Tooltip>
              </Link>
              <Typography
                color="textSecondary"
                variant="body2"
              >
                by
                {' '}
                <Link
                  color="textPrimary"
                  variant="subtitle2"
                >
                  {glossary.owner}
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
          <Grid
            container
          >
            <Grid
              item
              md={4}
              xs={12}
            >
              <Typography
                color="textSecondary"
                variant="body2"
              >
                <FaIcons.FaUsersCog />
                {' '}
                Team
              </Typography>
            </Grid>
            <Grid
              item
              md={8}
              xs={12}
            >
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
                <Tooltip title={glossary.admin || '-'}><span>{glossary.admin || '-'}</span></Tooltip>
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
          <Grid
            container
          >
            <Grid
              item
              md={4}
              xs={12}
            >
              <Typography
                color="textSecondary"
                variant="body2"
              >
                <BsBookmark />
                {' '}
                Categories
              </Typography>
            </Grid>
            <Grid
              item
              md={8}
              xs={6}
            >
              <Typography
                color="textPrimary"
                variant="body2"
              >
                {glossary.stats.categories}
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
          <Grid
            container
          >
            <Grid
              item
              md={4}
              xs={12}
            >
              <Typography
                color="textSecondary"
                variant="body2"
              >
                <BsTag />
                {' '}
                Terms
              </Typography>
            </Grid>
            <Grid
              item
              md={8}
              xs={12}
            >
              <Typography
                color="textPrimary"
                variant="body2"
              >
                {glossary.stats.terms}
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
            key={glossary.nodeUri}
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
              to={`/console/glossaries/${glossary.nodeUri}`}
            >
              Learn More
            </Button>
          </Box>
        </Box>
      </Card>
    </Grid>
  );
};
GlossaryListItem.propTypes = {
  glossary: PropTypes.object.isRequired
};
export default GlossaryListItem;
