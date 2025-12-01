import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { signOut, getCurrentUser } from 'aws-amplify/auth';
import ReceiptUpload from '../components/ReceiptUpload';
import './Dashboard.css';

const Dashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      console.error('Error loading user:', error);
    }
  };

  const handleLogout = async () => {
    try {
      await signOut();
      navigate('/login');
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };

  const handleUploadSuccess = () => {
    // Refresh expenses or show success message
    console.log('Receipt uploaded successfully!');
    // TODO: Refresh expense list
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>Smart Expense Monitor</h1>
          <button onClick={handleLogout} className="logout-button">
            Logout
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="dashboard-content">
          <div className="welcome-section">
            <h2>Welcome to Your Dashboard{user && `, ${user.username}`}</h2>
            <p>Upload your receipts and track your expenses here.</p>
          </div>

          <div className="upload-section-wrapper">
            <ReceiptUpload onUploadSuccess={handleUploadSuccess} />
          </div>

          <div className="dashboard-cards">

            <div className="dashboard-card">
              <h3>Monthly Report</h3>
              <p>View your monthly expense reports</p>
              <button className="card-button">View Report</button>
            </div>

            <div className="dashboard-card">
              <h3>Expense History</h3>
              <p>Browse through your expense history</p>
              <button className="card-button">View History</button>
            </div>
          </div>

          <div className="stats-section">
            <h3>Quick Stats</h3>
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-label">This Month</span>
                <span className="stat-value">$0.00</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Total Expenses</span>
                <span className="stat-value">$0.00</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Receipts Uploaded</span>
                <span className="stat-value">0</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;

