import { Box, CardMedia, Grid, Typography } from '@mui/material';

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
        <Typography variant="h5" color="#fff">
          &nbsp;Amazon ResearchZone
        </Typography>
      </Grid>
    </Grid>
  </>
);
