import React from 'react';
import PropTypes from 'prop-types';
import { THEMES, useSettings } from 'design';

export const TextDisplay = ({ text }) => {
  const { settings } = useSettings();

  const containerStyle = {
    width: '600px',
    height: '390px',
    maxWidth: '100%',
    margin: '0 auto',
    padding: '20px',
    border:
      settings.theme === THEMES.LIGHT ? '1px solid #eee' : '1px solid #333',
    borderRadius: '5px',
    backgroundColor: settings.theme === THEMES.LIGHT ? '#ffffff' : '#1e1e1e',
    color: settings.theme === THEMES.LIGHT ? '#333333' : '#d4d4d4',
    fontFamily: 'Arial, sans-serif',
    fontSize: '14px',
    lineHeight: '1.6',
    whiteSpace: 'pre-wrap',
    wordWrap: 'break-word',
    overflowY: 'auto',
    maxHeight: '400px'
  };

  return <div style={containerStyle}>{text}</div>;
};

TextDisplay.propTypes = {
  text: PropTypes.string.isRequired
};
