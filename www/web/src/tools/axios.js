// axios.js
import axios from 'axios';

const baseURL = import.meta.env.VITE_BASE_URL;

const instance = axios.create({
  baseURL: baseURL, // 使用环境变量设置的 baseURL
  timeout: 60000, // 设置超时时间（可选）
  // 其他 Axios 配置选项（可选）
});

export default instance;