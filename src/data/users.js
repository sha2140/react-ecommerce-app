// User credentials for authentication
export const users = [
  { username: 'spider', password: 'Spider@1234' },
  { username: 'vivek', password: 'spider4' },
  { username: 'sanjay', password: 'spider4' },
  { username: 'pankaj', password: 'spider4' },
  { username: 'shailesh', password: 'spider4' },
];

// Function to validate user credentials
export const validateUser = (username, password) => {
  return users.find(
    (user) => user.username === username && user.password === password
  );
};
