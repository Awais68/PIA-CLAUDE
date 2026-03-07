import express from 'express'
import { getServiceStatus, getSystemHealth, getSystemMetrics } from '../system-status.js'
import { readVaultFiles } from '../vault-reader.js'

const router = express.Router()

// GET system health
router.get('/health', (req, res) => {
  const health = getSystemHealth()
  res.json(health)
})

// GET services status
router.get('/services', (req, res) => {
  const services = getServiceStatus()
  res.json(services)
})

// GET system metrics
router.get('/metrics', (req, res) => {
  const metrics = getSystemMetrics()
  res.json(metrics)
})

// GET dashboard stats
router.get('/stats', (req, res) => {
  // Mock statistics
  const stats = {
    whatsapp: { incoming: 24, outgoing: 18, trend: 'up' },
    linkedin: { incoming: 45, outgoing: 12, trend: 'up' },
    facebook: { incoming: 18, outgoing: 5, trend: 'down' },
    instagram: { incoming: 67, outgoing: 23, trend: 'up' },
    gmail: { incoming: 156, outgoing: 89, trend: 'stable' },
    twitter: { incoming: 34, outgoing: 7, trend: 'up' },
  }
  
  // Count pending approvals
  const approvals = readVaultFiles('Pending_Approval')
  stats.pendingApprovals = approvals.length

  res.json(stats)
})

export default router
