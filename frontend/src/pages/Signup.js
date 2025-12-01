import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { signUp, confirmSignUp, resendSignUpCode } from 'aws-amplify/auth';
import './Auth.css';

const Signup = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    verificationCode: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [needsVerification, setNeedsVerification] = useState(false);
  const [resendingCode, setResendingCode] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError(''); // Clear error when user types
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    try {
      if (needsVerification) {
        // Confirm sign up with verification code
        const result = await confirmSignUp({
          username: formData.email,
          confirmationCode: formData.verificationCode
        });
        console.log('Verification result:', result);
        alert('Account verified successfully! You can now sign in.');
        navigate('/login');
      } else {
        // Sign up new user
        const result = await signUp({
          username: formData.email,
          password: formData.password,
          options: {
            userAttributes: {
              email: formData.email,
              name: formData.name
            }
          }
        });
        console.log('Signup result:', result);
        
        // Check if verification is required
        if (result.nextStep && result.nextStep.signUpStep === 'CONFIRM_SIGN_UP') {
          setNeedsVerification(true);
          setError(''); // Clear any previous errors
        } else {
          // If no verification needed, go to login
          navigate('/login');
        }
      }
    } catch (err) {
      console.error('Signup error:', err);
      console.error('Error details:', JSON.stringify(err, null, 2));
      
      // Handle existing unverified user
      if (err.name === 'UsernameExistsException' || err.message?.includes('already exists')) {
        // User exists but might be unverified - show verification form
        setNeedsVerification(true);
        setError('An account with this email already exists. Please enter the verification code sent to your email, or click "Resend Code" below.');
      } else if (err.name === 'InvalidPasswordException') {
        setError('Password does not meet requirements. Must be at least 8 characters with uppercase, lowercase, numbers, and symbols.');
      } else if (err.name === 'InvalidParameterException') {
        setError('Invalid email or password format. Please check your input.');
      } else if (err.name === 'CodeMismatchException' || err.message?.includes('Invalid verification code')) {
        setError('Invalid verification code. Please check the code and try again, or request a new code.');
      } else if (err.name === 'ExpiredCodeException' || err.message?.includes('expired')) {
        setError('Verification code has expired. Please request a new code.');
        setNeedsVerification(true);
      } else {
        setError(err.message || 'Failed to sign up. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    if (!formData.email) {
      setError('Please enter your email address first.');
      return;
    }

    setResendingCode(true);
    setError('');

    try {
      await resendSignUpCode({
        username: formData.email
      });
      alert('Verification code resent! Please check your email (including spam folder).');
      setNeedsVerification(true);
    } catch (err) {
      console.error('Resend code error:', err);
      if (err.name === 'UserNotFoundException') {
        setError('No account found with this email. Please sign up first.');
        setNeedsVerification(false);
      } else if (err.name === 'NotAuthorizedException' && err.message?.includes('Auto verification')) {
        setError('Code resend is not available. Please check your email for the original code, or contact support. You can also try signing up again with the same email.');
      } else if (err.name === 'InvalidParameterException') {
        setError('Please enter a valid email address.');
      } else if (err.name === 'LimitExceededException') {
        setError('Too many resend attempts. Please wait a few minutes before trying again.');
      } else {
        setError(err.message || 'Failed to resend code. Please try again.');
      }
    } finally {
      setResendingCode(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Smart Expense Monitor</h1>
          <h2>Create Account</h2>
          <p>Sign up to start tracking your expenses.</p>
        </div>
        
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="name">Full Name</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="Enter your full name"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Enter your email"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Create a password"
              required
            />
          </div>

          {!needsVerification ? (
            <>
              <div className="form-group">
                <label htmlFor="confirmPassword">Confirm Password</label>
                <input
                  type="password"
                  id="confirmPassword"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  placeholder="Confirm your password"
                  required
                />
              </div>
            </>
          ) : (
            <>
              <div className="form-group">
                <label htmlFor="verificationCode">Verification Code</label>
                <input
                  type="text"
                  id="verificationCode"
                  name="verificationCode"
                  value={formData.verificationCode}
                  onChange={handleChange}
                  placeholder="Enter verification code from email"
                  required
                  maxLength="6"
                  style={{ textAlign: 'center', letterSpacing: '0.5em', fontSize: '1.2em' }}
                />
                <p style={{ fontSize: '0.9em', marginTop: '5px', color: '#666' }}>
                  Check your email for the verification code
                </p>
              </div>
              
              <div style={{ marginTop: '10px', textAlign: 'center' }}>
                <button
                  type="button"
                  onClick={handleResendCode}
                  disabled={resendingCode || !formData.email}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: '#2575fc',
                    cursor: resendingCode || !formData.email ? 'not-allowed' : 'pointer',
                    textDecoration: 'underline',
                    fontSize: '0.9em',
                    padding: '5px'
                  }}
                >
                  {resendingCode ? 'Sending...' : "Didn't receive code? Resend"}
                </button>
              </div>
            </>
          )}

          {error && (
            <div className="error-message" style={{ color: 'red', marginBottom: '10px', padding: '10px', backgroundColor: '#ffe6e6', borderRadius: '5px' }}>
              {error}
            </div>
          )}

          {needsVerification && (
            <div style={{ 
              marginBottom: '10px', 
              padding: '12px', 
              backgroundColor: '#e6f3ff', 
              borderRadius: '5px', 
              fontSize: '0.9em',
              border: '1px solid #b3d9ff'
            }}>
              <strong>📧 Check your email!</strong>
              <br />
              A verification code has been sent to <strong>{formData.email}</strong>
              <br />
              <small style={{ color: '#666' }}>Don't forget to check your spam folder.</small>
            </div>
          )}

          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? 'Processing...' : needsVerification ? 'Verify Email' : 'Sign Up'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Signup;

