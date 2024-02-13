import { Box, CardMedia, Grid, Tooltip, Typography } from '@mui/material';
import version from '../../generated/version.json';

export const Logo = () => (
  <>
    <Grid container>
      <Grid item>
        <Box sx={{ mt: 0.5 }}>
          <CardMedia
            src="/static/logo-dataall.svg"
            component="img"
            sx={{
              height: '25px',
              width: '35px'
            }}
          />
        </Box>
      </Grid>
      <Grid item>
        <Tooltip title={'version ' + version.version} placement="top-start">
          <Typography variant="h5" color="#fff">
            &nbsp;data.all
          </Typography>
        </Tooltip>
      </Grid>
    </Grid>
  </>
);
