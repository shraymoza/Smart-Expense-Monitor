import React, { useEffect, useState } from 'react';
import { getExpenses } from '../services/api';
import './MonthlyReport.css';

const MonthlyReport = () => {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().slice(0, 7)); // YYYY-MM

  useEffect(() => {
    loadExpenses();
  }, [selectedMonth]);

  const loadExpenses = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getExpenses();
      const expensesList = Array.isArray(data) ? data : (data.items || []);
      
      // Filter expenses for selected month
      const monthExpenses = expensesList.filter(expense => {
        const expenseDate = expense.date || expense.createdAt;
        if (!expenseDate) return false;
        return expenseDate.startsWith(selectedMonth);
      });
      
      setExpenses(monthExpenses);
    } catch (err) {
      console.error('Error loading expenses:', err);
      setError(err.message || 'Failed to load expenses');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount || 0);
  };

  // Calculate totals
  const totalAmount = expenses.reduce((sum, expense) => sum + (parseFloat(expense.amount) || 0), 0);
  
  // Group by category
  const categoryTotals = expenses.reduce((acc, expense) => {
    const category = expense.category || 'Other';
    acc[category] = (acc[category] || 0) + (parseFloat(expense.amount) || 0);
    return acc;
  }, {});

  // Group by store
  const storeTotals = expenses.reduce((acc, expense) => {
    const store = expense.storeName || expense.store || 'Unknown Store';
    acc[store] = (acc[store] || 0) + (parseFloat(expense.amount) || 0);
    return acc;
  }, {});

  const monthName = new Date(selectedMonth + '-01').toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'long' 
  });

  if (loading) {
    return (
      <div className="monthly-report-container">
        <div className="loading">Loading report...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="monthly-report-container">
        <div className="error-message">{error}</div>
        <button onClick={loadExpenses} className="retry-button">Retry</button>
      </div>
    );
  }

  return (
    <div className="monthly-report-container">
      <div className="report-header">
        <h3>Monthly Expense Report</h3>
        <input
          type="month"
          value={selectedMonth}
          onChange={(e) => setSelectedMonth(e.target.value)}
          className="month-selector"
        />
      </div>

      <div className="report-summary">
        <div className="summary-card">
          <div className="summary-label">Total for {monthName}</div>
          <div className="summary-value">{formatCurrency(totalAmount)}</div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Number of Expenses</div>
          <div className="summary-value">{expenses.length}</div>
        </div>
      </div>

      {expenses.length === 0 ? (
        <div className="empty-state">
          <p>No expenses found for {monthName}. Upload receipts to see your expenses!</p>
        </div>
      ) : (
        <>
          {Object.keys(categoryTotals).length > 0 && (
            <div className="report-section">
              <h4>By Category</h4>
              <div className="totals-list">
                {Object.entries(categoryTotals)
                  .sort((a, b) => b[1] - a[1])
                  .map(([category, amount]) => (
                    <div key={category} className="total-item">
                      <span className="total-label">{category}</span>
                      <span className="total-value">{formatCurrency(amount)}</span>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {Object.keys(storeTotals).length > 0 && (
            <div className="report-section">
              <h4>By Store</h4>
              <div className="totals-list">
                {Object.entries(storeTotals)
                  .sort((a, b) => b[1] - a[1])
                  .slice(0, 10) // Top 10 stores
                  .map(([store, amount]) => (
                    <div key={store} className="total-item">
                      <span className="total-label">{store}</span>
                      <span className="total-value">{formatCurrency(amount)}</span>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default MonthlyReport;

