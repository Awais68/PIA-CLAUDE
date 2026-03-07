import os from 'os'
import { exec } from 'child_process'
import { promisify } from 'util'

const execAsync = promisify(exec)

// Service status tracking
const serviceStatus = {
  'Gmail Watcher': { status: 'running', startTime: Date.now(), lastActivity: Date.now() },
  'WhatsApp Watcher': { status: 'running', startTime: Date.now(), lastActivity: Date.now() },
  'LinkedIn Watcher': { status: 'warning', startTime: Date.now() - 60 * 60 * 1000, lastActivity: Date.now() - 45 * 60 * 1000 },
  'Cloud VM': { status: 'offline', startTime: null, lastActivity: null },
  'Odoo MCP': { status: 'running', startTime: Date.now(), lastActivity: Date.now() - 10 * 60 * 1000 },
  'Email MCP': { status: 'running', startTime: Date.now(), lastActivity: Date.now() - 5 * 60 * 1000 },
  'Social MCP': { status: 'running', startTime: Date.now(), lastActivity: Date.now() - 2 * 60 * 1000 },
}

export function getServiceStatus() {
  return Object.entries(serviceStatus).map(([name, data]) => {
    const uptime = data.startTime ? formatUptime(Date.now() - data.startTime) : '—'
    const lastActivity = data.lastActivity ? formatTime(Date.now() - data.lastActivity) : '—'
    
    return {
      name,
      status: data.status,
      uptime,
      lastActivity,
    }
  })
}

export function getSystemMetrics() {
  const totalMem = os.totalmem()
  const freeMem = os.freemem()
  const usedMem = totalMem - freeMem
  const cpus = os.cpus()
  
  return {
    cpu: {
      cores: cpus.length,
      model: cpus[0]?.model || 'Unknown',
    },
    memory: {
      total: Math.round(totalMem / 1024 / 1024 / 1024),
      used: Math.round(usedMem / 1024 / 1024 / 1024),
      free: Math.round(freeMem / 1024 / 1024 / 1024),
      percent: Math.round((usedMem / totalMem) * 100),
    },
    uptime: os.uptime(),
  }
}

export function getSystemHealth() {
  const metrics = getSystemMetrics()
  const services = getServiceStatus()
  
  const allRunning = services.every(s => s.status !== 'offline')
  const hasWarnings = services.some(s => s.status === 'warning')
  
  return {
    overall: hasWarnings ? 'warning' : allRunning ? 'ok' : 'critical',
    metrics,
    services,
    timestamp: new Date(),
  }
}

function formatUptime(ms) {
  const hours = Math.floor(ms / 3600000)
  const minutes = Math.floor((ms % 3600000) / 60000)
  return `${hours}h ${minutes}m`
}

function formatTime(ms) {
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(ms / 60000)
  const hours = Math.floor(ms / 3600000)
  const days = Math.floor(ms / 86400000)

  if (seconds < 60) return `${seconds}s ago`
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  return `${days}d ago`
}

// Update service status
export function updateServiceStatus(serviceName, status) {
  if (serviceStatus[serviceName]) {
    serviceStatus[serviceName].status = status
    serviceStatus[serviceName].lastActivity = Date.now()
    if (status === 'running' && !serviceStatus[serviceName].startTime) {
      serviceStatus[serviceName].startTime = Date.now()
    }
  }
}

export function recordServiceActivity(serviceName) {
  if (serviceStatus[serviceName]) {
    serviceStatus[serviceName].lastActivity = Date.now()
  }
}
