import React, { useState } from 'react';
import { getCurrentUser } from 'aws-amplify/auth';
import { getPresignedUploadUrl, uploadToS3 } from '../services/api';
import './ReceiptUpload.css';

const ReceiptUpload = ({ onUploadSuccess }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
  const maxFileSize = 10 * 1024 * 1024; // 10MB

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    if (!allowedTypes.includes(file.type)) {
      setError('Invalid file type. Please upload JPG, PNG, or PDF files only.');
      return;
    }

    // Validate file size
    if (file.size > maxFileSize) {
      setError('File size too large. Maximum size is 10MB.');
      return;
    }

    setSelectedFile(file);
    setError('');
    setSuccess(false);

    // Create preview for images
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(file);
    } else {
      setPreview(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first.');
      return;
    }

    setUploading(true);
    setError('');
    setSuccess(false);
    setUploadProgress(0);

    try {
      // Get current user for user ID
      const user = await getCurrentUser();
      console.log('Current user:', user);
      
      // Cognito user ID is in user.userId (sub claim)
      const userId = user.userId || user.username;
      console.log('Using userId:', userId);
      
      if (!userId) {
        throw new Error('Unable to get user ID. Please sign in again.');
      }

      // Generate unique file name
      const fileExtension = selectedFile.name.split('.').pop();
      const receiptId = `${Date.now()}-${Math.random().toString(36).substring(7)}`;
      const fileName = `users/${userId}/uploads/${receiptId}.${fileExtension}`;
      console.log('Generated fileName:', fileName);

      // Get presigned URL from API
      setUploadProgress(10);
      const response = await getPresignedUploadUrl(fileName, selectedFile.type);
      console.log('Presigned URL response:', response);
      
      // Handle different response structures
      let uploadUrl = response.uploadUrl || response.upload_url || response.url;
      
      // If response has a body property (API Gateway proxy format)
      if (!uploadUrl && response.body) {
        const bodyData = typeof response.body === 'string' ? JSON.parse(response.body) : response.body;
        uploadUrl = bodyData.uploadUrl || bodyData.upload_url || bodyData.url;
      }
      
      console.log('Extracted uploadUrl:', uploadUrl);
      
      if (!uploadUrl || uploadUrl === 'undefined') {
        console.error('Full response object:', JSON.stringify(response, null, 2));
        throw new Error('Presigned URL not found in response. Check console for details.');
      }

      // Upload to S3
      setUploadProgress(30);
      console.log('Uploading to S3 URL:', uploadUrl.substring(0, 100) + '...');
      await uploadToS3(uploadUrl, selectedFile);

      setUploadProgress(100);
      setSuccess(true);
      setSelectedFile(null);
      setPreview(null);

      // Reset file input
      const fileInput = document.getElementById('receipt-file-input');
      if (fileInput) fileInput.value = '';

      // Call success callback
      if (onUploadSuccess) {
        onUploadSuccess();
      }

      // Reset success message after 3 seconds
      setTimeout(() => {
        setSuccess(false);
        setUploadProgress(0);
      }, 3000);
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message || 'Failed to upload receipt. Please try again.');
      setUploadProgress(0);
    } finally {
      setUploading(false);
    }
  };

  const handleRemove = () => {
    setSelectedFile(null);
    setPreview(null);
    setError('');
    setSuccess(false);
    setUploadProgress(0);
    const fileInput = document.getElementById('receipt-file-input');
    if (fileInput) fileInput.value = '';
  };

  return (
    <div className="receipt-upload-container">
      <div className="upload-section">
        <h3>Upload Receipt</h3>
        
        {!selectedFile ? (
          <div className="file-input-wrapper">
            <label htmlFor="receipt-file-input" className="file-input-label">
              <div className="upload-icon">📄</div>
              <div className="upload-text">
                <strong>Click to select a file</strong>
                <span>or drag and drop</span>
              </div>
              <div className="upload-hint">
                JPG, PNG, or PDF (Max 10MB)
              </div>
            </label>
            <input
              id="receipt-file-input"
              type="file"
              accept=".jpg,.jpeg,.png,.pdf"
              onChange={handleFileSelect}
              className="file-input"
            />
          </div>
        ) : (
          <div className="file-preview-container">
            {preview ? (
              <div className="image-preview">
                <img src={preview} alt="Receipt preview" />
              </div>
            ) : (
              <div className="file-info">
                <div className="file-icon">📄</div>
                <div className="file-name">{selectedFile.name}</div>
                <div className="file-size">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </div>
              </div>
            )}
            
            <div className="file-actions">
              <button
                type="button"
                onClick={handleRemove}
                className="remove-button"
                disabled={uploading}
              >
                Remove
              </button>
              <button
                type="button"
                onClick={handleUpload}
                className="upload-button"
                disabled={uploading}
              >
                {uploading ? 'Uploading...' : 'Upload Receipt'}
              </button>
            </div>

            {uploading && (
              <div className="upload-progress">
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
                <div className="progress-text">{uploadProgress}%</div>
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {success && (
          <div className="success-message">
            ✅ Receipt uploaded successfully! Processing...
          </div>
        )}
      </div>
    </div>
  );
};

export default ReceiptUpload;

