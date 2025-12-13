import React, { useEffect, useState } from 'react';
import { getExpenses, updateExpenseCategory } from '../services/api';
import './ExpenseList.css';

const ExpenseList = () => {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedId, setExpandedId] = useState(null);
  const [editingCategory, setEditingCategory] = useState(null);
  const [newCategory, setNewCategory] = useState('');
  const [updating, setUpdating] = useState(false);
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState('All');
  
  const categories = [
    'Groceries',
    'Food & Drink',
    'Pharmacy',
    'Home Improvement',
    'Electronics',
    'Gas & Fuel',
    'Shopping',
    'Discount Store',
    'Other'
  ];

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

  const handleCategoryEdit = (expense) => {
    setEditingCategory(expense.expenseId);
    setNewCategory(expense.category || 'Other');
  };

  const handleCategoryCancel = () => {
    setEditingCategory(null);
    setNewCategory('');
  };

  const handleCategorySave = async (expenseId) => {
    if (!newCategory) {
      setError('Please select a category');
      return;
    }

    try {
      setUpdating(true);
      setError('');
      await updateExpenseCategory(expenseId, newCategory);
      
      // Update local state
      setExpenses(expenses.map(exp => 
        exp.expenseId === expenseId 
          ? { ...exp, category: newCategory }
          : exp
      ));
      
      setEditingCategory(null);
      setNewCategory('');
    } catch (err) {
      console.error('Error updating category:', err);
      setError(err.message || 'Failed to update category');
    } finally {
      setUpdating(false);
    }
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

  // Filter expenses by category
  const filteredExpenses = selectedCategoryFilter === 'All'
    ? expenses
    : expenses.filter(expense => (expense.category || 'Other') === selectedCategoryFilter);

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
        <div className="header-actions">
          <select
            value={selectedCategoryFilter}
            onChange={(e) => setSelectedCategoryFilter(e.target.value)}
            className="category-filter-select"
          >
            <option value="All">All Categories</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          <button onClick={loadExpenses} className="refresh-button">Refresh</button>
        </div>
      </div>
      
      {filteredExpenses.length === 0 && expenses.length > 0 && (
        <div className="empty-state">
          <p>No expenses found in the "{selectedCategoryFilter}" category.</p>
        </div>
      )}
      
      <div className="expense-list">
        {filteredExpenses.map((expense) => {
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
                      {editingCategory === expense.expenseId ? (
                        <div className="category-edit-container">
                          <select
                            value={newCategory}
                            onChange={(e) => setNewCategory(e.target.value)}
                            className="category-select"
                            disabled={updating}
                          >
                            {categories.map(cat => (
                              <option key={cat} value={cat}>{cat}</option>
                            ))}
                          </select>
                          <div className="category-edit-buttons">
                            <button
                              onClick={() => handleCategorySave(expense.expenseId)}
                              className="save-category-btn"
                              disabled={updating}
                            >
                              {updating ? 'Saving...' : 'Save'}
                            </button>
                            <button
                              onClick={handleCategoryCancel}
                              className="cancel-category-btn"
                              disabled={updating}
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="category-display">
                          <span className="detail-value">{expense.category || 'Other'}</span>
                          <button
                            onClick={() => handleCategoryEdit(expense)}
                            className="edit-category-btn"
                            title="Edit category"
                          >
                            ✏️
                          </button>
                        </div>
                      )}
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

