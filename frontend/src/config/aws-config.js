// AWS Configuration for Smart Expense Monitor
// This file loads configuration from Terraform outputs

// Import Terraform outputs (you may need to adjust the path)
// For now, we'll use the values directly from the deployment
const awsConfig = {
  region: 'us-east-1',
  userPoolId: 'us-east-1_1QQRZs2xC',
  userPoolWebClientId: '2satntb5hl1fkr1rboa9ohsf7j',
  apiGatewayUrl: 'https://pr53ispmk7.execute-api.us-east-1.amazonaws.com/dev',
  s3BucketName: 'smart-expense-monitor-receipts'
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

// For localhost development - works with any port
export const getCallbackUrls = () => {
  const port = window.location.port || '3000';
  const origin = window.location.origin;
  return [
    `${origin}`,
    `${origin}/callback`,
    `http://localhost:${port}`,
    `http://localhost:${port}/callback`
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

