import api from './api'

export const authService = {
  async register(data) {
    const res = await api.post('/auth/register', data)
    return res.data
  },

  async login(username, password) {
    const res = await api.post('/auth/login', { username, password })
    localStorage.setItem('access_token',  res.data.access_token)
    localStorage.setItem('refresh_token', res.data.refresh_token)
    return res.data
  },

  async getMe() {
    const res = await api.get('/auth/me')
    return res.data
  },

  async changePassword(current_password, new_password) {
    const res = await api.post('/auth/change-password', {
      current_password,
      new_password
    })
    return res.data
  },

  logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    window.location.href = '/login'
  }
}
