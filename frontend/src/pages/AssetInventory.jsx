import { useState, useEffect, useCallback } from 'react'
import api from '../services/api'
import { Search, Edit2, X, Check } from 'lucide-react'

const CRITICALITY_OPTIONS = ['critical', 'high', 'medium', 'low']

function EditModal({ asset, onSave, onClose }) {
  const [form, setForm] = useState({
    criticality: asset.criticality || 'medium',
    owner_team:  asset.owner_team  || '',
    asset_type:  asset.asset_type  || '',
    notes:       asset.notes       || '',
    tags:        asset.tags?.join(', ') || '',
  })
  const [saving, setSaving] = useState(false)
  const [error,  setError]  = useState('')

  const save = async () => {
    setSaving(true)
    setError('')
    try {
      await api.patch(`/assets/${asset.id}`, {
        criticality: form.criticality,
        owner_team:  form.owner_team  || null,
        asset_type:  form.asset_type  || null,
        notes:       form.notes       || null,
        tags:        form.tags
          ? form.tags.split(',').map(t => t.trim()).filter(Boolean)
          : null,
      })
      onSave()
    } catch (err) {
      setError(err.response?.data?.detail || 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-md flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h3 className="text-white font-semibold">
            Edit Asset — {asset.ip_address}
          </h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300">
            <X size={18}/>
          </button>
        </div>

        {error && (
          <div className="bg-red-900 border border-red-700 text-red-300 text-sm px-3 py-2 rounded-lg">
            {error}
          </div>
        )}

        <div>
          <label className="text-gray-400 text-sm mb-1 block">Criticality</label>
          <select
            className="input"
            value={form.criticality}
            onChange={e => setForm(f => ({ ...f, criticality: e.target.value }))}
          >
            {CRITICALITY_OPTIONS.map(c => (
              <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-gray-400 text-sm mb-1 block">Asset Type</label>
          <input
            className="input"
            placeholder="e.g. server, workstation, router"
            value={form.asset_type}
            onChange={e => setForm(f => ({ ...f, asset_type: e.target.value }))}
          />
        </div>

        <div>
          <label className="text-gray-400 text-sm mb-1 block">Owner Team</label>
          <input
            className="input"
            placeholder="e.g. DevOps, Security, IT"
            value={form.owner_team}
            onChange={e => setForm(f => ({ ...f, owner_team: e.target.value }))}
          />
        </div>

        <div>
          <label className="text-gray-400 text-sm mb-1 block">
            Tags <span className="text-gray-600">(comma separated)</span>
          </label>
          <input
            className="input"
            placeholder="e.g. production, linux, web"
            value={form.tags}
            onChange={e => setForm(f => ({ ...f, tags: e.target.value }))}
          />
        </div>

        <div>
          <label className="text-gray-400 text-sm mb-1 block">Notes</label>
          <textarea
            className="input resize-none h-20"
            placeholder="Any notes about this asset..."
            value={form.notes}
            onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
          />
        </div>

        <div className="flex gap-3 pt-2">
          <button
            className="btn-primary flex-1 flex items-center justify-center gap-2"
            onClick={save}
            disabled={saving}
          >
            {saving ? (
              <>
                <span className="animate-spin rounded-full h-4 w-4 border-t-2 border-white"/>
                Saving...
              </>
            ) : (
              <><Check size={15}/> Save Changes</>
            )}
          </button>
          <button className="btn-ghost" onClick={onClose}>Cancel</button>
        </div>
      </div>
    </div>
  )
}

export default function AssetInventory() {
  const [assets,      setAssets]      = useState([])
  const [summary,     setSummary]     = useState(null)
  const [search,      setSearch]      = useState('')
  const [criticality, setCriticality] = useState('')
  const [loading,     setLoading]     = useState(true)
  const [editAsset,   setEditAsset]   = useState(null)

  const load = useCallback(async (q = '', crit = '') => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (q)    params.append('search',      q)
      if (crit) params.append('criticality', crit)

      const [assets, sum] = await Promise.all([
        api.get(`/assets/?${params.toString()}`),
        api.get('/assets/stats/summary'),
      ])
      setAssets(assets.data.assets || [])
      setSummary(sum.data)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleSearch = e => {
    e.preventDefault()
    load(search, criticality)
  }

  const handleCritFilter = val => {
    setCriticality(val)
    load(search, val)
  }

  const critColor = {
    critical: 'badge-critical',
    high:     'badge-high',
    medium:   'badge-medium',
    low:      'badge-low',
  }

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-sky-500"/>
    </div>
  )

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-xl font-bold text-white">Asset Inventory</h2>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="card">
            <span className="text-gray-500 text-xs uppercase">Total Assets</span>
            <span className="text-2xl font-bold text-sky-400">{summary.total_assets}</span>
          </div>
          <div className="card">
            <span className="text-gray-500 text-xs uppercase">Critical</span>
            <span className="text-2xl font-bold text-red-400">{summary.critical_assets}</span>
          </div>
          <div className="card">
            <span className="text-gray-500 text-xs uppercase">High Risk</span>
            <span className="text-2xl font-bold text-orange-400">{summary.high_risk}</span>
          </div>
          <div className="card">
            <span className="text-gray-500 text-xs uppercase">High Criticality</span>
            <span className="text-2xl font-bold text-yellow-400">
              {summary.by_criticality?.high || 0}
            </span>
          </div>
        </div>
      )}

      {/* Search + Filter */}
      <div className="flex flex-col md:flex-row gap-3">
        <form onSubmit={handleSearch} className="flex gap-2 flex-1">
          <div className="relative flex-1">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500"/>
            <input
              className="input pl-9"
              placeholder="Search by IP or hostname..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <button className="btn-primary">Search</button>
        </form>

        {/* Criticality Filter */}
        <div className="flex gap-2">
          <button
            onClick={() => handleCritFilter('')}
            className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
              criticality === ''
                ? 'border-sky-500 bg-sky-900 text-sky-300'
                : 'border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600'
            }`}
          >
            All
          </button>
          {CRITICALITY_OPTIONS.map(c => (
            <button
              key={c}
              onClick={() => handleCritFilter(c)}
              className={`text-xs px-3 py-1.5 rounded-lg border transition-colors capitalize ${
                criticality === c
                  ? 'border-sky-500 bg-sky-900 text-sky-300'
                  : 'border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600'
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 text-xs uppercase border-b border-gray-800">
              <th className="text-left py-2 pr-4">IP Address</th>
              <th className="text-left py-2 pr-4">Hostname</th>
              <th className="text-left py-2 pr-4">OS</th>
              <th className="text-left py-2 pr-4">Type</th>
              <th className="text-left py-2 pr-4">Owner</th>
              <th className="text-left py-2 pr-4">Criticality</th>
              <th className="text-left py-2 pr-4">Risk Score</th>
              <th className="text-left py-2 pr-4">Last Seen</th>
              <th className="text-left py-2">Edit</th>
            </tr>
          </thead>
          <tbody>
            {assets.map(a => (
              <tr
                key={a.id}
                className="border-b border-gray-800 hover:bg-gray-800 transition-colors"
              >
                <td className="py-2 pr-4 font-mono text-sky-400">{a.ip_address}</td>
                <td className="py-2 pr-4 text-gray-300">{a.hostname || '—'}</td>
                <td className="py-2 pr-4 text-gray-400 max-w-xs truncate">{a.os_name || '—'}</td>
                <td className="py-2 pr-4 text-gray-400">{a.asset_type || '—'}</td>
                <td className="py-2 pr-4 text-gray-400">{a.owner_team || '—'}</td>
                <td className="py-2 pr-4">
                  <span className={critColor[a.criticality] || 'badge-info'}>
                    {a.criticality || '—'}
                  </span>
                </td>
                <td className="py-2 pr-4">
                  <div className="flex items-center gap-2">
                    <div className="w-12 bg-gray-800 rounded-full h-1.5">
                      <div
                        className={`h-1.5 rounded-full ${
                          (a.last_risk_score || 0) >= 60 ? 'bg-red-500' :
                          (a.last_risk_score || 0) >= 30 ? 'bg-yellow-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${Math.min(a.last_risk_score || 0, 100)}%` }}
                      />
                    </div>
                    <span className="text-gray-300 text-xs">
                      {a.last_risk_score?.toFixed(1) || '0.0'}
                    </span>
                  </div>
                </td>
                <td className="py-2 pr-4 text-gray-500 text-xs">
                  {a.last_seen ? new Date(a.last_seen).toLocaleDateString() : '—'}
                </td>
                <td className="py-2">
                  <button
                    onClick={() => setEditAsset(a)}
                    className="text-gray-600 hover:text-sky-400 transition-colors p-1"
                  >
                    <Edit2 size={14}/>
                  </button>
                </td>
              </tr>
            ))}
            {!assets.length && (
              <tr>
                <td colSpan={9} className="py-12 text-center text-gray-500">
                  No assets found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Edit Modal */}
      {editAsset && (
        <EditModal
          asset={editAsset}
          onSave={() => { setEditAsset(null); load(search, criticality) }}
          onClose={() => setEditAsset(null)}
        />
      )}
    </div>
  )
}
