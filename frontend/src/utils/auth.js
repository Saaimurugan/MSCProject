// Authentication utility functions

export const getUser = () => {
  const userStr = localStorage.getItem('user');
  if (userStr) {
    try {
      return JSON.parse(userStr);
    } catch (e) {
      return null;
    }
  }
  return null;
};

export const isAuthenticated = () => {
  return getUser() !== null;
};

export const isAdmin = () => {
  const user = getUser();
  return user && user.role === 'admin';
};

export const isStudent = () => {
  const user = getUser();
  return user && user.role === 'student';
};

export const logout = () => {
  localStorage.removeItem('user');
};

export const getUserRole = () => {
  const user = getUser();
  return user ? user.role : null;
};

export const getUsername = () => {
  const user = getUser();
  return user ? user.username : null;
};
