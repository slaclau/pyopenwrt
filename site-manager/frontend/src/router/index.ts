// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import { ElNotification } from 'element-plus'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/login',
            name: 'Login',
            component: () => import('@/views/LoginView.vue'),
        },
        {
            path: '/',
            name: 'Dashboard',
            component: () => import('@/views/DashboardView.vue'),
            meta: { requiresAuth: true } // 🔒 Protected route flag
        }
    ]
})

// Global route guard to check auth status before changing pages
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('auth_token') // Or use a Pinia store

    if (to.meta.requiresAuth && !token) {
        ElNotification({
            title: 'Access Denied',
            message: 'Please log in to access this page.',
            type: 'error'
        })
        next({ name: 'Login', query: { redirect: to.fullPath } })
    } else {
        next()
    }
})

export default router
