import api from './api'

export const reportService = {
  async generateReport(scanId, reportType = 'pdf') {
    const res = await api.post('/reports/generate', {
      scan_id:     scanId,
      report_type: reportType,
      include_evidence: true
    })
    return res.data
  },

  async listReports() {
    const res = await api.get('/reports/')
    return res.data
  },

  async getReport(reportId) {
    const res = await api.get(`/reports/${reportId}`)
    return res.data
  },

  async deleteReport(reportId) {
    const res = await api.delete(`/reports/${reportId}`)
    return res.data
  }
}
