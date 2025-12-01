import React, { useEffect, useState } from 'react';
import { getExpenses } from '../services/api';
import './ExpenseList.css';

const ExpenseList = () => {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    loadExpenses();
  }, []);

  const loadExpenses = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getExpenses();
      // Handle both array and object responses
      const expensesList = Array.isArray(data) ? data : (data.items || []);
      setExpenses(expensesList);
    } catch (err) {
      console.error('Error loading expenses:', err);
      setError(err.message || 'Failed to load expenses');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      });
    } catch {
      return dateString;
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
      <div className="expense-list-container">
        <div className="loading">Loading expenses...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="expense-list-container">
        <div className="error-message">{error}</div>
        <button onClick={loadExpenses} className="retry-button">Retry</button>
      </div>
    );
  }

  if (expenses.length === 0) {
    return (
      <div className="expense-list-container">
        <div className="empty-state">
          <p>No expenses found. Upload receipts to see your expenses here!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="expense-list-container">
      <div className="expense-list-header">
        <h3>Expense History</h3>
        <button onClick={loadExpenses} className="refresh-button">Refresh</button>
      </div>
      
      <div className="expense-list">
        {expenses.map((expense) => {
          const isExpanded = expandedId === expense.expenseId;
          return (
            <div 
              key={expense.expenseId} 
              className={`expense-item ${isExpanded ? 'expanded' : ''}`}
            >
              <div 
                className="expense-item-header"
                onClick={() => setExpandedId(isExpanded ? null : expense.expenseId)}
              >
                <div className="expense-main">
                  <div className="expense-store">{expense.storeName || expense.store || 'Unknown Store'}</div>
                  <div className="expense-amount">{formatCurrency(expense.amount)}</div>
                </div>
                <div className="expense-details">
                  <span className="expense-date">{formatDate(expense.date || expense.createdAt)}</span>
                  {expense.category && (
                    <span className="expense-category">{expense.category}</span>
                  )}
                  <span className="expand-icon">{isExpanded ? '▼' : '▶'}</span>
                </div>
              </div>
              
              {isExpanded && (
                <div className="expense-expanded-content">
                  <div className="expense-details-section">
                    <h4>Receipt Details</h4>
                    <div className="detail-row">
                      <span className="detail-label">Store:</span>
                      <span className="detail-value">{expense.storeName || expense.store || 'Unknown Store'}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">Date:</span>
                      <span className="detail-value">{formatDate(expense.date || expense.createdAt)}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">Category:</span>
                      <span className="detail-value">{expense.category || 'Other'}</span>
                    </div>
                    <div className="detail-row">
                      <span className="detail-label">Total Amount:</span>
                      <span className="detail-value amount-highlight">{formatCurrency(expense.amount)}</span>
                    </div>
                    {expense.receiptS3Key && (
                      <div className="detail-row">
                        <span className="detail-label">Receipt ID:</span>
                        <span className="detail-value receipt-id">{expense.expenseId}</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="expense-items-section">
                    <h4>Items {expense.items && expense.items.length > 0 && `(${expense.items.length})`}</h4>
                    {expense.items && expense.items.length > 0 ? (
                      <div className="items-list">
                        <div className="items-header">
                          <span className="item-name-header">Item</span>
                          <span className="item-qty-header">Qty</span>
                          <span className="item-price-header">Price</span>
                          <span className="item-subtotal-header">Subtotal</span>
                        </div>
                        {expense.items.map((item, index) => (
                          <div key={index} className="item-row">
                            <span className="item-name">{item.name || 'Unknown Item'}</span>
                            <span className="item-qty">{item.quantity || 1}</span>
                            <span className="item-price">{formatCurrency(item.price || 0)}</span>
                            <span className="item-subtotal">{formatCurrency(item.subtotal || item.price || 0)}</span>
                          </div>
                        ))}
                        <div className="items-total">
                          <span className="items-total-label">Items Total:</span>
                          <span className="items-total-amount">
                            {formatCurrency(expense.items.reduce((sum, item) => sum + (item.subtotal || item.price || 0), 0))}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="items-placeholder">
                        <p>No items extracted from this receipt.</p>
                        <p className="items-note">Items may not be available for older receipts or if extraction failed.</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ExpenseList;

