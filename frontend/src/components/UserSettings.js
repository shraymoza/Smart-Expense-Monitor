import React, { useEffect, useState } from 'react';
import { getUserSettings, updateUserSettings } from '../services/api';
import { getCurrentUser, fetchUserAttributes } from 'aws-amplify/auth';
import './UserSettings.css';

const UserSettings = () => {
  const [threshold, setThreshold] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const user = await getCurrentUser();
      // Try to get email from user attributes
      const attributes = await fetchUserAttributes();
      setEmail(attributes.email || user.username || '');
      
      const settings = await getUserSettings();
      if (settings && settings.monthlyThreshold) {
        setThreshold(settings.monthlyThreshold.toString());
      }
    } catch (error) {
      console.error('Error loading settings:', error);
      setMessage({ type: 'error', text: 'Failed to load settings' });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    
    if (!threshold || parseFloat(threshold) <= 0) {
      setMessage({ type: 'error', text: 'Please enter a valid threshold amount' });
      return;
    }

    try {
      setSaving(true);
      setMessage({ type: '', text: '' });
      
      await updateUserSettings({
        monthlyThreshold: parseFloat(threshold),
        emailNotifications: true
      });
      
      setMessage({ type: 'success', text: 'Settings saved successfully!' });
    } catch (error) {
      console.error('Error saving settings:', error);
      setMessage({ type: 'error', text: error.message || 'Failed to save settings' });
    } finally {
      setSaving(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  if (loading) {
    return (
      <div className="settings-container">
        <div className="loading">Loading settings...</div>
      </div>
    );
  }

  return (
    <div className="settings-container">
      <div className="settings-header">
        <h3>Notification Settings</h3>
        <p>Set your monthly expense threshold to receive email notifications</p>
      </div>

      <form onSubmit={handleSave} className="settings-form">
        <div className="form-group">
          <label htmlFor="email">Email Address</label>
          <input
            type="email"
            id="email"
            value={email}
            disabled
            className="disabled-input"
          />
          <small>This is your registered email address for notifications</small>
        </div>

        <div className="form-group">
          <label htmlFor="threshold">Monthly Expense Threshold</label>
          <div className="input-with-symbol">
            <span className="currency-symbol">$</span>
            <input
              type="number"
              id="threshold"
              value={threshold}
              onChange={(e) => {
                setThreshold(e.target.value);
                setMessage({ type: '', text: '' });
              }}
              placeholder="0.00"
              min="0"
              step="0.01"
              required
            />
          </div>
          <small>
            You'll receive an email notification when your monthly expenses exceed this amount
          </small>
        </div>

        {message.text && (
          <div className={`message ${message.type}`}>
            {message.text}
          </div>
        )}

        <button type="submit" className="save-button" disabled={saving}>
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </form>

      <div className="settings-info">
        <h4>How it works:</h4>
        <ul>
          <li>Set your monthly spending limit above</li>
          <li>You'll receive an email when your expenses exceed the threshold</li>
          <li>Notifications are sent at the end of each month</li>
          <li>You can update your threshold anytime</li>
        </ul>
      </div>
    </div>
  );
};

export default UserSettings;

