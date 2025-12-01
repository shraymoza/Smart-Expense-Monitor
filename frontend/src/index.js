import React from 'react';
import ReactDOM from 'react-dom/client';
import { Amplify } from 'aws-amplify';
import { cognitoConfig } from './config/aws-config';
import './index.css';
import App from './App';

// Configure AWS Amplify
Amplify.configure(cognitoConfig);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

