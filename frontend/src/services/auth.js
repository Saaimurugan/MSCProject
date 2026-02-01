import jwtDecode from 'jwt-decode';

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
    return user ? JSON.parse(user) : null;
  },

  // Check if user is authenticated
  isAuthenticated: () => {
    const token = AuthService.getToken();
    if (!token) return false;

    try {
      const decoded = jwtDecode(token);
      const currentTime = Date.now() / 1000;
      return decoded.exp > currentTime;
    } catch (error) {
      return false;
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