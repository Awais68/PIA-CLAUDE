import express from 'express'
import { WebSocketServer } from 'ws'
import { createServer } from 'http'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'
import { existsSync } from 'fs'
import dotenv from 'dotenv'
import chokidar from 'chokidar'

// Import routes
import approvalsRouter from './routes/approvals.js'
import emailsRouter from './routes/emails.js'
import draftsRouter from './routes/drafts.js'
import socialRouter from './routes/social.js'
import systemRouter from './routes/system.js'
import logsRouter from './routes/logs.js'

dotenv.config()

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const PORT = process.env.PORT || 3000

const app = express()
const server = createServer(app)
const wss = new WebSocketServer({ server })

// Middleware
app.use(express.json())

// Serve static files if dist exists, otherwise skip (use Vite dev server)
const distPath = join(__dirname, '../dist')
if (existsSync(distPath)) {
  app.use(express.static(distPath))
}

// API Routes
app.use('/api/approvals', approvalsRouter)
app.use('/api/emails', emailsRouter)
app.use('/api/drafts', draftsRouter)
app.use('/api/social', socialRouter)
app.use('/api/system', systemRouter)
app.use('/api/logs', logsRouter)

// Serve React app (only if dist exists)
if (existsSync(join(distPath, 'index.html'))) {
  app.get('/*', (req, res) => {
    res.sendFile(join(distPath, 'index.html'))
  })
}

// WebSocket Connection
wss.on('connection', (ws) => {
  console.log('WebSocket client connected')

  ws.on('message', (message) => {
    console.log('Received:', message)
  })

  ws.on('close', () => {
    console.log('WebSocket client disconnected')
  })
})

// Vault file watcher - emit WebSocket events on changes
const vaultPath = process.env.VAULT_PATH
if (vaultPath) {
  const watcher = chokidar.watch(vaultPath, {
    ignored: /(^|[\/\\])\.|node_modules/,
    persistent: true,
    awaitWriteFinish: {
      stabilityThreshold: 2000,
      pollInterval: 100,
    },
  })

  watcher.on('add', (path) => {
    broadcast({ type: 'vault_change', action: 'add', path })
  })

  watcher.on('change', (path) => {
    broadcast({ type: 'vault_change', action: 'change', path })
  })

  watcher.on('unlink', (path) => {
    broadcast({ type: 'vault_change', action: 'delete', path })
  })
}

// Broadcast to all connected clients
function broadcast(message) {
  wss.clients.forEach((client) => {
    if (client.readyState === 1) { // WebSocket.OPEN
      client.send(JSON.stringify(message))
    }
  })
}

// Global broadcast function for use in routes
global.broadcast = broadcast

// Start servers
server.listen(PORT, () => {
  console.log(`[HTTP] Server running on http://localhost:${PORT}`)
  console.log(`[WebSocket] Server running on ws://localhost:${PORT}`)
})

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down...')
  server.close(() => console.log('HTTP server closed'))
  wss.close(() => console.log('WebSocket server closed'))
})
