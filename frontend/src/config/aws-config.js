// AWS Configuration for Smart Expense Monitor
// This file loads configuration from environment variables (for Amplify) or uses defaults (for local dev)
// Environment variables are set in Amplify Console or .env file

const awsConfig = {
  region: process.env.REACT_APP_AWS_REGION || 'us-east-1',
  userPoolId: process.env.REACT_APP_COGNITO_USER_POOL_ID || 'us-east-1_x07pvpdFQ',
  userPoolWebClientId: process.env.REACT_APP_COGNITO_CLIENT_ID || '1qlbj29cvm48uc4mrc2ckvgdoj',
  apiGatewayUrl: process.env.REACT_APP_API_GATEWAY_URL || 'https://ky2q08cneh.execute-api.us-east-1.amazonaws.com/dev',
  s3BucketName: process.env.REACT_APP_S3_BUCKET_NAME || 'smart-expense-monitor-receipts'
};

// Cognito configuration for AWS Amplify v5
export const cognitoConfig = {
  Auth: {
    Cognito: {
      userPoolId: awsConfig.userPoolId,
      userPoolClientId: awsConfig.userPoolWebClientId,
      region: awsConfig.region,
      loginWith: {
        email: true
      },
      signUpVerificationMethod: 'code',
      userAttributes: {
        email: {
          required: true
        },
        name: {
          required: false
        }
      }
    }
  }
};

// For localhost development and Amplify - works with any port/domain
export const getCallbackUrls = () => {
  const origin = window.location.origin;
  const port = window.location.port;
  
  // For Amplify (production), use the actual domain
  if (origin.includes('amplifyapp.com') || origin.includes('amplifyapp')) {
    return [
      origin,
      `${origin}/callback`
    ];
  }
  
  // For localhost development
  return [
    origin,
    `${origin}/callback`,
    `http://localhost:${port || '3000'}`,
    `http://localhost:${port || '3000'}/callback`
  ];
};

// API Gateway configuration
export const apiConfig = {
  apiGatewayUrl: awsConfig.apiGatewayUrl,
  endpoints: {
    receipts: `${awsConfig.apiGatewayUrl}/receipts`,
    expenses: `${awsConfig.apiGatewayUrl}/expenses`
  }
};

// S3 configuration
export const s3Config = {
  bucketName: awsConfig.s3BucketName,
  region: awsConfig.region
};

export default awsConfig;
