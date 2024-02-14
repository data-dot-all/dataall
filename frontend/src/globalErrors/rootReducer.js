import { combineReducers } from '@reduxjs/toolkit';
import { errorReducer } from 'globalErrors/errorReducer';

export const rootReducer = combineReducers({
  error: errorReducer
});
