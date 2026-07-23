<script setup lang="ts">
import { reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { site_manager_client } from '@/client'
import { loginForAccessTokenUsersTokenPost } from '@/sdk'

const router = useRouter()
const route = useRoute()

const form = reactive({
    username: '',
    password: ''
})

const handleLogin = async () => {
    if (form.username && form.password) {
        let response = (await loginForAccessTokenUsersTokenPost({ client: site_manager_client, body: { username: form.username, password: form.password } }))
        let token = response.data?.access_token;
        if (!response.error && token) {
            localStorage.setItem('auth_token', token)
            console.log(token)
            ElMessage.success('Logged in')

            // Redirect back or to dashboard
            const target = (route.query.redirect as string) || '/'
            router.push(target)
        } else {
            ElMessage.error('Invalid credentials')
        }
    } else {
        ElMessage.error('Please fill in all fields')

    }
}
</script>

<template>
    <div style="max-width: 320px; margin: 100px auto;">
        <h1>Login</h1>
        <el-form label-position="top">
            <el-form-item label="Username">
                <el-input v-model="form.username" placeholder="Username" />
            </el-form-item>

            <el-form-item label="Password">
                <el-input v-model="form.password" type="password" placeholder="Password" />
            </el-form-item>

            <el-button type="primary" style="width: 100%" @click="handleLogin">
                Login
            </el-button>
        </el-form>
    </div>
</template>