import React, { useEffect, useState } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import { getExpenses } from '../services/api';
import './MonthlyReport.css';

const MonthlyReport = () => {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectionMode, setSelectionMode] = useState('month'); // 'month' or 'range'
  const [dateRange, setDateRange] = useState([new Date(), null]); // Initialize with current date
  const [startDate, endDate] = dateRange;

  useEffect(() => {
    loadExpenses();
  }, [dateRange]);

  const loadExpenses = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getExpenses();
      const expensesList = Array.isArray(data) ? data : (data.items || []);
      
      // Filter expenses based on date range or month
      let filteredExpenses = expensesList;
      
      if (selectionMode === 'month' && startDate) {
        // Filter by month
        const year = startDate.getFullYear();
        const month = String(startDate.getMonth() + 1).padStart(2, '0');
        const monthPrefix = `${year}-${month}`;
        
        filteredExpenses = expensesList.filter(expense => {
          const expenseDate = expense.date || expense.createdAt;
          if (!expenseDate) return false;
          return expenseDate.startsWith(monthPrefix);
        });
      } else if (selectionMode === 'range' && startDate && endDate) {
        // Filter by date range
        const start = new Date(startDate);
        start.setHours(0, 0, 0, 0);
        const end = new Date(endDate);
        end.setHours(23, 59, 59, 999);
        
        filteredExpenses = expensesList.filter(expense => {
          const expenseDate = expense.date || expense.createdAt;
          if (!expenseDate) return false;
          const expDate = new Date(expenseDate);
          return expDate >= start && expDate <= end;
        });
      } else if (startDate) {
        // If only start date is selected, show that month
        const year = startDate.getFullYear();
        const month = String(startDate.getMonth() + 1).padStart(2, '0');
        const monthPrefix = `${year}-${month}`;
        
        filteredExpenses = expensesList.filter(expense => {
          const expenseDate = expense.date || expense.createdAt;
          if (!expenseDate) return false;
          return expenseDate.startsWith(monthPrefix);
        });
      }
      
      setExpenses(filteredExpenses);
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

  const getDateRangeLabel = () => {
    if (selectionMode === 'month' && startDate) {
      return startDate.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long' 
      });
    } else if (selectionMode === 'range' && startDate && endDate) {
      return `${startDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })} - ${endDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
    } else if (startDate) {
      return startDate.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long' 
      });
    }
    return 'All Time';
  };

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
        <h3>Expense Report</h3>
        <div className="date-picker-container">
          <div className="selection-mode-toggle">
            <button
              className={`mode-btn ${selectionMode === 'month' ? 'active' : ''}`}
              onClick={() => {
                setSelectionMode('month');
                setDateRange([startDate || new Date(), null]);
              }}
            >
              Month
            </button>
            <button
              className={`mode-btn ${selectionMode === 'range' ? 'active' : ''}`}
              onClick={() => {
                setSelectionMode('range');
                setDateRange([startDate || new Date(), null]);
              }}
            >
              Date Range
            </button>
          </div>
          {selectionMode === 'month' ? (
            <DatePicker
              selected={startDate}
              onChange={(date) => setDateRange([date, null])}
              dateFormat="MMMM yyyy"
              showMonthYearPicker
              showFullMonthYearPicker
              placeholderText="Select month"
              className="date-picker-input"
              wrapperClassName="date-picker-wrapper"
            />
          ) : (
            <DatePicker
              selected={startDate}
              onChange={(update) => setDateRange(update)}
              startDate={startDate}
              endDate={endDate}
              selectsRange
              dateFormat="MMM dd, yyyy"
              placeholderText="Select date range"
              className="date-picker-input"
              wrapperClassName="date-picker-wrapper"
            />
          )}
        </div>
      </div>

      <div className="report-summary">
        <div className="summary-card">
          <div className="summary-label">Total for {getDateRangeLabel()}</div>
          <div className="summary-value">{formatCurrency(totalAmount)}</div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Number of Expenses</div>
          <div className="summary-value">{expenses.length}</div>
        </div>
      </div>

      {expenses.length === 0 ? (
        <div className="empty-state">
          <p>No expenses found for {getDateRangeLabel()}. Upload receipts to see your expenses!</p>
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

