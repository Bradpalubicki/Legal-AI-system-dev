/**
 * Authentication Utilities for k6 Load Tests
 */

import http from 'k6/http';
import { check } from 'k6';
import { config, getHttpOptions } from '../config.js';

/**
 * Login and get authentication token
 * @returns {string|null} Auth token or null if login failed
 */
export function login() {
  const url = `${config.baseUrl}${config.endpoints.auth.login}`;
  const payload = JSON.stringify({
    email: config.testUser.email,
    password: config.testUser.password,
  });

  const response = http.post(url, payload, getHttpOptions());

  const loginSuccess = check(response, {
    'login successful': (r) => r.status === 200,
    'login returns token': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.access_token !== undefined;
      } catch (e) {
        return false;
      }
    },
  });

  if (loginSuccess && response.status === 200) {
    try {
      const body = JSON.parse(response.body);
      return body.access_token;
    } catch (e) {
      console.error('Failed to parse login response:', e);
      return null;
    }
  }

  return null;
}

/**
 * Verify token is valid by fetching user profile
 * @param {string} token - Auth token to verify
 * @returns {boolean} True if token is valid
 */
export function verifyToken(token) {
  const url = `${config.baseUrl}${config.endpoints.auth.me}`;
  const response = http.get(url, getHttpOptions(token));

  return check(response, {
    'token is valid': (r) => r.status === 200,
  });
}

/**
 * Logout (invalidate token)
 * @param {string} token - Auth token to invalidate
 * @returns {boolean} True if logout successful
 */
export function logout(token) {
  const url = `${config.baseUrl}${config.endpoints.auth.logout}`;
  const response = http.post(url, null, getHttpOptions(token));

  return check(response, {
    'logout successful': (r) => r.status === 200,
  });
}

/**
 * Register a new test user
 * @param {string} email - User email
 * @param {string} password - User password
 * @returns {boolean} True if registration successful
 */
export function register(email, password) {
  const url = `${config.baseUrl}${config.endpoints.auth.register}`;
  const payload = JSON.stringify({
    email: email,
    password: password,
    full_name: `Load Test User ${Date.now()}`,
  });

  const response = http.post(url, payload, getHttpOptions());

  return check(response, {
    'registration successful': (r) => r.status === 201 || r.status === 200,
  });
}

export default {
  login,
  verifyToken,
  logout,
  register,
};
