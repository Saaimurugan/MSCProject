import React from 'react';

// Custom JWT decoder (no external library needed)
const decodeJWT = (token) => {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      throw new Error('Invalid token format');
    }
    
    // Decode the payload (second part)
    const payload = parts[1];
    // Add padding if needed
    const paddedPayload = payload + '='.repeat((4 - payload.length % 4) % 4);
    const decoded = atob(paddedPayload.replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(decoded);
  } catch (error) {
    console.error('JWT decode error:', error);
    return null;
  }
};

export const AuthService = {
  // Store token and user data
  setAuth: (token, user) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
  },

  // Get stored token
  getToken: () => {
    return localStorage.getItem('token');
  },

  // Get stored user data
  getUser: () => {
    const user = localStorage.getItem('user');
    if (!user || user === 'undefined') return null;
    try {
      return JSON.parse(user);
    } catch (error) {
      console.error('Error parsing user data:', error);
      return null;
    }
  },

  // Check if user is authenticated
  isAuthenticated: () => {
    const token = AuthService.getToken();
    if (!token) return false;

    try {
      const decoded = decodeJWT(token);
      if (!decoded) {
        // If decode fails, check if token exists and user exists as fallback
        const user = AuthService.getUser();
        return !!(token && user);
      }
      
      const currentTime = Date.now() / 1000;
      return decoded.exp > currentTime;
    } catch (error) {
      console.error('JWT validation error:', error);
      // If decode fails, check if token exists and user exists as fallback
      const user = AuthService.getUser();
      return !!(token && user);
    }
  },

  // Check if user has specific role
  hasRole: (role) => {
    const user = AuthService.getUser();
    return user && user.role === role;
  },

  // Check if user has any of the specified roles
  hasAnyRole: (roles) => {
    const user = AuthService.getUser();
    return user && roles.includes(user.role);
  },

  // Logout user
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  },

  // Get user role
  getUserRole: () => {
    const user = AuthService.getUser();
    return user ? user.role : null;
  }
};