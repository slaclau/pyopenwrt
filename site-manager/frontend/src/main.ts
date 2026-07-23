// if you just want to import css
import './style/index.scss'

import 'element-plus/theme-chalk/dark/css-vars.css'

import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router' // 1. Import your router setup

const app = createApp(App)
app.use(ElementPlus)
app.use(router)

app.config.globalProperties.window = window

app.mount('#app')
