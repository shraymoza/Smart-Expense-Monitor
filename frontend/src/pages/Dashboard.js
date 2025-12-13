import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { signOut, getCurrentUser, fetchUserAttributes } from 'aws-amplify/auth';
import ReceiptUpload from '../components/ReceiptUpload';
import ExpenseList from '../components/ExpenseList';
import MonthlyReport from '../components/MonthlyReport';
import UserSettings from '../components/UserSettings';
import { getExpenses } from '../services/api';
import './Dashboard.css';

const Dashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [userName, setUserName] = useState('');
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState('dashboard'); // 'dashboard', 'history', 'report'
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    loadUser();
    loadExpenses();
  }, []);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const loadUser = async () => {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      
      // Get user attributes to find name
      try {
        const attributes = await fetchUserAttributes();
        // Try to get name from attributes (name, given_name, or username as fallback)
        const name = attributes.name || attributes.given_name || attributes['custom:name'] || currentUser.username || '';
        setUserName(name);
      } catch (attrError) {
        // Fallback to username if attributes can't be fetched
        setUserName(currentUser.username || '');
      }
    } catch (error) {
      console.error('Error loading user:', error);
    }
  };

  const loadExpenses = async () => {
    try {
      setLoading(true);
      const data = await getExpenses();
      const expensesList = Array.isArray(data) ? data : (data.items || []);
      setExpenses(expensesList);
    } catch (error) {
      console.error('Error loading expenses:', error);
      setExpenses([]);
    } finally {
      setLoading(false);
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
    console.log('Receipt uploaded successfully!');
    // Wait a few seconds for Lambda to process, then refresh
    setTimeout(() => {
      loadExpenses();
    }, 3000);
  };

  // Calculate stats
  const currentMonth = new Date().toISOString().slice(0, 7); // YYYY-MM
  const monthlyExpenses = expenses.filter(exp => {
    const date = exp.date || exp.createdAt;
    return date && date.startsWith(currentMonth);
  });
  
  const monthlyTotal = monthlyExpenses.reduce((sum, exp) => sum + (parseFloat(exp.amount) || 0), 0);
  const totalExpenses = expenses.reduce((sum, exp) => sum + (parseFloat(exp.amount) || 0), 0);
  const receiptsCount = expenses.length;

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  const handleSettingsClick = () => {
    setActiveView('settings');
    setShowMenu(false);
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>Smart Expense Monitor</h1>
          <div className="header-actions" ref={menuRef}>
            <button 
              onClick={() => setShowMenu(!showMenu)}
              className="gear-icon-button"
              title="Settings"
            >
              ⚙️
            </button>
            {showMenu && (
              <div className="settings-dropdown">
                <button 
                  onClick={handleSettingsClick}
                  className="dropdown-item"
                >
                  Settings
                </button>
                <button 
                  onClick={handleLogout}
                  className="dropdown-item"
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="dashboard-content">
          <div className="welcome-section">
            <h2>Welcome to Your Dashboard{userName && `, ${userName}`}</h2>
            <p>Upload your receipts and track your expenses here.</p>
          </div>

          <div className="upload-section-wrapper">
            <ReceiptUpload onUploadSuccess={handleUploadSuccess} />
          </div>

          <div className="dashboard-cards">
            <div className="dashboard-card">
              <h3>Monthly Report</h3>
              <p>View your monthly expense reports</p>
              <button 
                className="card-button"
                onClick={() => setActiveView(activeView === 'report' ? 'dashboard' : 'report')}
              >
                {activeView === 'report' ? 'Back to Dashboard' : 'View Report'}
              </button>
            </div>

            <div className="dashboard-card">
              <h3>Expense History</h3>
              <p>Browse through your expense history</p>
              <button 
                className="card-button"
                onClick={() => setActiveView(activeView === 'history' ? 'dashboard' : 'history')}
              >
                {activeView === 'history' ? 'Back to Dashboard' : 'View History'}
              </button>
            </div>
          </div>

          {activeView === 'dashboard' && (
            <div className="stats-section">
              <h3>Quick Stats</h3>
              <div className="stats-grid">
                <div className="stat-item">
                  <span className="stat-label">This Month</span>
                  <span className="stat-value">{formatCurrency(monthlyTotal)}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Total Expenses</span>
                  <span className="stat-value">{formatCurrency(totalExpenses)}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Receipts Uploaded</span>
                  <span className="stat-value">{receiptsCount}</span>
                </div>
              </div>
            </div>
          )}

          {activeView === 'history' && (
            <div className="view-section">
              <ExpenseList />
            </div>
          )}

          {activeView === 'report' && (
            <div className="view-section">
              <MonthlyReport />
            </div>
          )}

          {activeView === 'settings' && (
            <div className="view-section">
              <UserSettings />
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;

