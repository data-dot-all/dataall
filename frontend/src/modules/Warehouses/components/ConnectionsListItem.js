import { Box, Button, Card, Grid, Typography } from '@mui/material';
import PropTypes from 'prop-types';
import { useCardStyle } from 'design';

export const ConnectionsListItem = ({ connection }) => {
  const classes = useCardStyle();

  return (
    <Card
      key={connection.connectionUri}
      className={classes.card}
      sx={{
        mt: 2
      }}
    >
      <Grid container spacing={0.5} alignItems="center">
        <Grid item justifyContent="center" md={1} lg={1} xl={1}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography color="textPrimary" variant="body1">
              Name
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              {`${connection.name}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="center" md={2} lg={2} xl={2}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography color="textPrimary" variant="body1">
              warehouse Identifier
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              {`${connection.warehouseId}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="center" md={2} lg={2} xl={2}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography color="textPrimary" variant="body1">
              warehouse Type
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              {`${connection.warehouseType}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="center" md={1} lg={1} xl={1}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography color="textPrimary" variant="body1">
              Team
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              {`${connection.SamlAdminGroupName}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="center" md={1} lg={1} xl={1}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography color="textPrimary" variant="body1">
              Type
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              {`${connection.type}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="center" md={3} lg={3} xl={3}>
          <Box
            sx={{
              pt: 2,
              pb: 2,
              px: 3
            }}
          >
            <Typography color="textPrimary" variant="body1">
              Details
            </Typography>
            <Typography
              color="textSecondary"
              variant="body1"
              style={{ wordWrap: 'break-word' }}
            >
              {`${connection.content}`}
            </Typography>
          </Box>
        </Grid>
        <Grid item justifyContent="center" md={1} lg={1} xl={1}>
          <Button
            color="primary"
            type="button"
            // TODO implement edit
            //onClick={handleEditModalOpen}
            variant="contained"
          >
            Edit
          </Button>
        </Grid>
        <Grid item justifyContent="center" md={1} lg={1} xl={1}>
          <Button
            color="primary"
            type="button"
            // TODO implement delete
            //onClick={deleteConnection}
            variant="contained"
          >
            Delete
          </Button>
        </Grid>
      </Grid>
    </Card>
  );
};
ConnectionsListItem.propTypes = {
  connection: PropTypes.object.isRequired
};
