import api from './api'

export const scanService = {

  // ── Start Scan ─────────────────────────────────────────
  async startScan(targets, profile = 'standard', extraArgs = '') {
    const res = await api.post('/scan/start', {
      targets,
      profile,
      extra_args: extraArgs   // ← fixed field name
    })
    return res.data
  },

  // ── List Scans ─────────────────────────────────────────
  async listScans() {
    const res = await api.get('/scan/list')
    return res.data
  },

  // ── Get Single Scan ────────────────────────────────────
  async getScan(scanId) {
    const res = await api.get(`/scan/${scanId}`)
    return res.data
  },

  // ── Get Scan Results ───────────────────────────────────
  async getScanResults(scanId) {
    const res = await api.get(`/scan/${scanId}/results`)
    return res.data
  },

  // ── Delete Scan ────────────────────────────────────────
  async deleteScan(scanId) {
    const res = await api.delete(`/scan/${scanId}`)
    return res.data
  },

  // ── Stop Scan (marks as failed/deleted) ───────────────
  async stopScan(scanId) {
    const res = await api.delete(`/scan/${scanId}`)
    return res.data
  },

  // ── Compare Scans ──────────────────────────────────────
  async compareScans(scanIdA, scanIdB) {
    const res = await api.get(`/dashboard/compare/${scanIdA}/${scanIdB}`)
    return res.data
  },

  // ── WebSocket — fixed URL, full handlers ──────────────
  connectWebSocket(scanId, { onMessage, onOpen, onClose, onError } = {}) {
    const token    = localStorage.getItem('access_token')
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host     = window.location.hostname
    const port     = window.location.port

    // Use same host/port as page — vite proxy handles /ws → backend
    // In Docker, nginx handles /ws → backend
    const wsUrl = port
      ? `${protocol}//${host}:${port}/ws/scan/${scanId}?token=${token}`
      : `${protocol}//${host}/ws/scan/${scanId}?token=${token}`

    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log(`✅ WebSocket connected — scan #${scanId}`)
      if (onOpen) onOpen()
    }

    ws.onmessage = e => {
      try {
        const data = JSON.parse(e.data)
        if (onMessage) onMessage(data)
      } catch (err) {
        console.error('WebSocket parse error:', err)
      }
    }

    ws.onerror = e => {
      console.error(`❌ WebSocket error — scan #${scanId}`, e)
      if (onError) onError(e)
    }

    ws.onclose = e => {
      console.log(`🔌 WebSocket closed — scan #${scanId} code=${e.code}`)
      if (onClose) onClose(e)
    }

    return ws
  }
}
