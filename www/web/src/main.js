import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import axios from './tools/axios'; // 引入你的 Axios 实例
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'


const app = createApp(App)
app.config.globalProperties.$axios = axios;

app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.mount('#app')
