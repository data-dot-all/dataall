import { combineReducers } from '@reduxjs/toolkit';
import { errorReducer } from './errorReducer';

const rootReducer = combineReducers({
  error: errorReducer
});

export default rootReducer;
