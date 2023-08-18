export const SET_ERROR = 'SET_ERROR';
export const HIDE_ERROR = 'HIDE_ERROR';

const initState = {
  error: null,
  isOpen: false
};

export const errorReducer = function (state = initState, action) {
  const { error } = action;

  if (error) {
    return {
      error,
      isOpen: true
    };
  }
  if (action.type === HIDE_ERROR) {
    return {
      error: null,
      isOpen: false
    };
  }
  return state;
};
