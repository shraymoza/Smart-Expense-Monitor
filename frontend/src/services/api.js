// API Service for Smart Expense Monitor
// Handles all API Gateway requests with Cognito authentication

import { fetchAuthSession } from 'aws-amplify/auth';
import { apiConfig } from '../config/aws-config';

/**
 * Get authentication headers for API requests
 */
async function getAuthHeaders() {
  try {
    const session = await fetchAuthSession();
    const token = session.tokens?.idToken?.toString();
    
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    };
  } catch (error) {
    console.error('Error getting auth session:', error);
    throw new Error('Not authenticated');
  }
}

/**
 * Make authenticated API request
 */
async function apiRequest(endpoint, method = 'GET', body = null) {
  const headers = await getAuthHeaders();
  const url = `${apiConfig.apiGatewayUrl}${endpoint}`;

  const options = {
    method,
    headers,
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const errorText = await response.text();
      let errorData;
      try {
        errorData = JSON.parse(errorText);
      } catch {
        errorData = { message: errorText || response.statusText };
      }
      throw new Error(errorData.message || `API request failed: ${response.statusText}`);
    }

    const responseText = await response.text();
    console.log('API Response:', responseText);
    
    try {
      return JSON.parse(responseText);
    } catch (e) {
      console.error('Failed to parse JSON response:', responseText);
      throw new Error('Invalid JSON response from server');
    }
  } catch (error) {
    console.error('API request error:', error);
    throw error;
  }
}

/**
 * Get presigned URL for S3 upload
 */
export async function getPresignedUploadUrl(fileName, fileType) {
  try {
    console.log('Requesting presigned URL for:', { fileName, fileType });
    const response = await apiRequest(
      '/receipts',
      'POST',
      {
        fileName,
        fileType
      }
    );
    console.log('Presigned URL response received:', response);
    
    // Handle different possible response structures
    if (response.uploadUrl) {
      return response;
    } else if (response.body) {
      // If response is wrapped in body (API Gateway proxy)
      const parsed = typeof response.body === 'string' ? JSON.parse(response.body) : response.body;
      return parsed;
    } else {
      console.error('Unexpected response structure:', response);
      throw new Error('Invalid response format from server');
    }
  } catch (error) {
    console.error('Error getting presigned URL:', error);
    throw error;
  }
}

/**
 * Upload file to S3 using presigned URL
 */
export async function uploadToS3(presignedUrl, file) {
  try {
    console.log('Uploading to S3:', {
      url: presignedUrl?.substring(0, 100) + '...',
      fileType: file.type,
      fileSize: file.size
    });
    
    if (!presignedUrl || presignedUrl === 'undefined' || typeof presignedUrl !== 'string') {
      throw new Error(`Invalid presigned URL: ${presignedUrl}. Expected a valid URL string.`);
    }
    
    // Validate URL format
    try {
      new URL(presignedUrl);
    } catch (e) {
      throw new Error(`Invalid URL format: ${presignedUrl}`);
    }
    
    const response = await fetch(presignedUrl, {
      method: 'PUT',
      body: file,
      headers: {
        'Content-Type': file.type,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('S3 upload failed:', {
        status: response.status,
        statusText: response.statusText,
        error: errorText,
        url: presignedUrl.substring(0, 100)
      });
      throw new Error(`Upload failed: ${response.statusText} (${response.status})`);
    }

    console.log('S3 upload successful');
    return true;
  } catch (error) {
    console.error('Error uploading to S3:', error);
    throw error;
  }
}

/**
 * Get user expenses
 */
export async function getExpenses() {
  try {
    console.log('Fetching expenses...');
    const response = await apiRequest('/expenses');
    // Handle both direct array and wrapped responses
    if (Array.isArray(response)) {
      return response;
    } else if (response.body) {
      // If response is wrapped in body (API Gateway proxy)
      const parsed = typeof response.body === 'string' ? JSON.parse(response.body) : response.body;
      return Array.isArray(parsed) ? parsed : (parsed.items || []);
    } else if (response.items) {
      return response.items;
    }
    return [];
  } catch (error) {
    console.error('Error fetching expenses:', error);
    throw error;
  }
}

/**
 * Get expense by ID
 */
export async function getExpense(expenseId) {
  try {
    return await apiRequest(`/expenses/${expenseId}`);
  } catch (error) {
    console.error('Error fetching expense:', error);
    throw error;
  }
}

/**
 * Get receipt metadata
 */
export async function getReceipts() {
  try {
    return await apiRequest('/receipts');
  } catch (error) {
    console.error('Error fetching receipts:', error);
    throw error;
  }
}

/**
 * Get user settings
 */
export async function getUserSettings() {
  try {
    console.log('Fetching user settings...');
    return await apiRequest('/settings');
  } catch (error) {
    console.error('Error fetching user settings:', error);
    throw error;
  }
}

/**
 * Update user settings
 */
export async function updateUserSettings(settings) {
  try {
    console.log('Updating user settings...', settings);
    return await apiRequest('/settings', 'PUT', settings);
  } catch (error) {
    console.error('Error updating user settings:', error);
    throw error;
  }
}

/**
 * Update expense category
 */
export async function updateExpenseCategory(expenseId, category) {
  try {
    console.log('Updating expense category...', { expenseId, category });
    return await apiRequest(`/expenses/${expenseId}`, 'PUT', { category });
  } catch (error) {
    console.error('Error updating expense category:', error);
    throw error;
  }
}

/**
 * Update expense items
 */
export async function updateExpenseItems(expenseId, items) {
  try {
    console.log('Updating expense items...', { expenseId, items });
    const response = await apiRequest(`/expenses/${expenseId}`, 'PUT', { items });
    return response;
  } catch (error) {
    console.error('Error updating expense items:', error);
    throw error;
  }
}

/**
 * Update expense (supports both category and items)
 */
export async function updateExpense(expenseId, updates) {
  try {
    console.log('Updating expense...', { expenseId, updates });
    return await apiRequest(`/expenses/${expenseId}`, 'PUT', updates);
  } catch (error) {
    console.error('Error updating expense:', error);
    throw error;
  }
}

