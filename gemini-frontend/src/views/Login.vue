<template>
  <div class="login-container">
    <h1>Login</h1>
    <div v-if="error" class="error-message">{{ error }}</div>
    <div v-if="successMessage" class="success-message">{{ successMessage }}</div>
    <form @submit.prevent="login">
      <div class="form-group">
        <label for="email">Email</label>
        <input type="email" id="email" v-model="email" required>
      </div>
      <div class="form-group">
        <label for="password">Password</label>
        <input type="password" id="password" v-model="password" required>
      </div>
      <div class="buttons">
        <button type="submit" :disabled="isLoading">
          {{ isLoading ? 'Logging in...' : 'Login' }}
        </button>
      </div>
    </form>
    <p class="auth-link">
      Don't have an account? <router-link to="/register">Register here</router-link>
    </p>
  </div>
</template>
<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { auth } from '../firebase'
import { signInWithEmailAndPassword, createUserWithEmailAndPassword } from 'firebase/auth'
import { ensureUserInDatabase } from '../services/userService'
export default {
  name: 'LoginPage',
  setup() {
    const email = ref('')
    const password = ref('')
    const error = ref(null)
    const successMessage = ref(null)
    const loading = ref(false)
    const router = useRouter()
    const login = async () => {
      loading.value = true
      error.value = null
      successMessage.value = null
      try {
        const userCredential = await signInWithEmailAndPassword(auth, email.value, password.value)
        // Ensure user exists in database but don't throw if it fails
        try {
          await ensureUserInDatabase(userCredential.user)
        } catch (dbErr) {
        }
        router.push('/')
      } catch (err) {
        if (err.code === 'auth/user-not-found') {
          error.value = 'User not found. Please check your email or register.'
        } else if (err.code === 'auth/wrong-password') {
          error.value = 'Incorrect password. Please try again.'
        } else {
          error.value = 'Login failed: ' + (err.message || 'Unknown error')
        }
      } finally {
        loading.value = false
      }
    }
    // Test account function
    const useTestAccount = async () => {
      loading.value = true
      error.value = null
      successMessage.value = null
      const testEmail = 'test@example.com'
      const testPassword = 'test123456'
      try {
        // Try to log in with test account
        try {
          const userCredential = await signInWithEmailAndPassword(auth, testEmail, testPassword)
          try {
            await ensureUserInDatabase(userCredential.user)
          } catch (dbErr) {
          }
          router.push('/')
          return
        } catch (loginErr) {
          // If login fails, try to create the test account
          if (loginErr.code === 'auth/user-not-found') {
            try {
              const userCredential = await createUserWithEmailAndPassword(auth, testEmail, testPassword)
              successMessage.value = 'Demo account created! Logging in...'
              try {
                await ensureUserInDatabase(userCredential.user)
              } catch (dbErr) {
              }
              // Wait a moment then redirect
              setTimeout(() => {
                router.push('/')
              }, 1500)
              return
            } catch (createErr) {
              if (createErr.code === 'auth/email-already-in-use') {
                // This shouldn't happen but handle it anyway
                error.value = 'Test account exists but login failed. Please try again.'
              } else {
                throw createErr
              }
            }
          } else {
            throw loginErr
          }
        }
      } catch (err) {
        error.value = 'Failed to use demo account: ' + (err.message || 'Unknown error')
      } finally {
        loading.value = false
      }
    }
    return {
      email,
      password,
      error,
      successMessage,
      loading,
      login,
      useTestAccount
    }
  }
}
</script>
<style scoped>
.login-container {
  max-width: 400px;
  margin: 40px auto;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}
h1 {
  margin-top: 0;
  color: #4285F4;
}
.form-group {
  margin-bottom: 15px;
  text-align: left;
}
label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}
.error-message {
  color: #f44336;
  margin-bottom: 15px;
  padding: 10px;
  background-color: #ffebee;
  border-radius: 4px;
}
.success-message {
  color: #4CAF50;
  margin-bottom: 15px;
  padding: 10px;
  background-color: #e8f5e9;
  border-radius: 4px;
}
input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}
button {
  width: 100%;
  padding: 12px;
  background-color: #4285F4;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.3s;
}
button:hover:not(:disabled) {
  background-color: #3367d6;
}
button:disabled {
  background-color: #9bb8ea;
  cursor: not-allowed;
}
.buttons {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.register-link {
  margin-top: 15px;
  color: #4285F4;
  text-decoration: none;
}
.register-link:hover {
  text-decoration: underline;
}
.demo-account {
  margin-top: 25px;
  padding-top: 15px;
  border-top: 1px solid #eee;
  text-align: center;
}
.test-account-btn {
  background-color: #34A853;
}
.test-account-btn:hover:not(:disabled) {
  background-color: #2e8f49;
}
</style> 