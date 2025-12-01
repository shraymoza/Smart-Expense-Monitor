import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Dashboard.css';

const Dashboard = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    // Logout logic will be implemented with Cognito
    navigate('/login');
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
            <h2>Welcome to Your Dashboard</h2>
            <p>Upload your receipts and track your expenses here.</p>
          </div>

          <div className="dashboard-cards">
            <div className="dashboard-card">
              <h3>Upload Receipt</h3>
              <p>Upload your daily receipts from various stores</p>
              <button className="card-button">Upload</button>
            </div>

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

