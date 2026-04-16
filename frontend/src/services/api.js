import axios from 'axios';

const createClient = (baseURL) => {
  const client = axios.create({ baseURL });
  
  client.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  client.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.clear();
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  );

  return client;
};

// Services distributed across specific ports
export const authApi = createClient('http://localhost:8001');
export const resumeApi = createClient('http://localhost:8002');
export const interviewApi = createClient('http://localhost:8003');
