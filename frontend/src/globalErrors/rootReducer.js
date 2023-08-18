import { combineReducers } from '@reduxjs/toolkit';
import { errorReducer } from './errorReducer';

export const rootReducer = combineReducers({
  error: errorReducer
});
