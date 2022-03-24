import { useContext } from 'react';
import LocalContext from '../contexts/LocalContext';
import AuthContext from '../contexts/AmplifyContext';

const useAuth = () => (!process.env.REACT_APP_COGNITO_USER_POOL_ID ? useContext(LocalContext) : useContext(AuthContext));

export default useAuth;
