import PropTypes from 'prop-types';
import { Navigate } from 'react-router-dom';
import { useAuth } from 'authentication';

export const GuestGuard = ({ children }) => {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated) {
    return <Navigate to="/console" />;
  }

  return <>{children}</>;
};

GuestGuard.propTypes = {
  children: PropTypes.node
};
