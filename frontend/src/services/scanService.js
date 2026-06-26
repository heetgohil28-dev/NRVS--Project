import api from './api'

export const scanService = {
  async startScan(targets, profile = "standard", customArgs = "") {
    const res = await api.post("/scan/start", { targets, profile, custom_args: customArgs })
    return res.data
  },

  async listScans() {
    const res = await api.get('/scan/list')
    return res.data
  },

  async getScan(scanId) {
    const res = await api.get(`/scan/${scanId}`)
    return res.data
  },

  async getScanResults(scanId) {
    const res = await api.get(`/scan/${scanId}/results`)
    return res.data
  },

  async deleteScan(scanId) {
    const res = await api.delete(`/scan/${scanId}`)
    return res.data
  },

  async compareScans(scanIdA, scanIdB) {
    const res = await api.get(`/dashboard/compare/${scanIdA}/${scanIdB}`)
    return res.data
  },

  connectWebSocket(scanId, onMessage) {
    const token = localStorage.getItem('access_token')
    const ws = new WebSocket(
      `ws://${window.location.hostname}:8000/ws/scan/${scanId}?token=${token}`
    )
    ws.onmessage = e => onMessage(JSON.parse(e.data))
    ws.onerror   = e => console.error('WebSocket error:', e)
    return ws
  }
}
