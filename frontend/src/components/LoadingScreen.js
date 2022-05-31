import { useEffect } from 'react';
import NProgress from 'nprogress';
import { Box } from '@mui/material';

const LoadingScreen = () => {
  useEffect(() => {
    NProgress.start();

    return () => {
      NProgress.done();
    };
  }, []);

  return (
    <Box
      sx={{
        backgroundColor: 'background.paper',
        minHeight: '100%'
      }}
    />
  );
};

export default LoadingScreen;
