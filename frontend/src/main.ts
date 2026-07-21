// if you just want to import css
import 'controller/style/index.scss'

import 'element-plus/theme-chalk/dark/css-vars.css'

import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'

const app = createApp(App)
app.use(ElementPlus)

app.config.globalProperties.window = window

app.mount('#app')
