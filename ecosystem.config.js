/**
 * Zoya - PM2 Ecosystem Configuration
 * Manages all watchers and orchestrator processes
 *
 * Usage:
 *   pm2 start ecosystem.config.js
 *   pm2 status
 *   pm2 logs
 *   pm2 save (for boot-time persistence)
 */

const path = require('path');
const projectDir = __dirname;

module.exports = {
  apps: [
    // ============================================================
    // 1. FILE SYSTEM WATCHER
    // Monitors AI_Employee_Vault/Inbox for new documents
    // ============================================================
    {
      name: 'zoya-watcher',
      script: 'uv',
      args: 'run zoya-watcher',
      cwd: projectDir,
      instances: 1,
      exec_mode: 'fork',

      // Auto-restart on crash
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      max_memory_restart: '500M',

      // Logging
      out_file: path.join(projectDir, 'AI_Employee_Vault/Logs/pm2-watcher-out.log'),
      error_file: path.join(projectDir, 'AI_Employee_Vault/Logs/pm2-watcher-err.log'),
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',

      // Environment
      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1',
      },

      // Graceful shutdown
      kill_timeout: 5000,
      listen_timeout: 3000,
      shutdown_with_message: true,
    },

    // ============================================================
    // 2. GMAIL WATCHER
    // Monitors Gmail inbox for incoming emails
    // ============================================================
    {
      name: 'zoya-gmail',
      script: 'uv',
      args: 'run zoya-gmail',
      cwd: projectDir,
      instances: 1,
      exec_mode: 'fork',

      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      max_memory_restart: '400M',

      out_file: path.join(projectDir, 'AI_Employee_Vault/Logs/pm2-gmail-out.log'),
      error_file: path.join(projectDir, 'AI_Employee_Vault/Logs/pm2-gmail-err.log'),
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',

      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1',
      },

      kill_timeout: 5000,
      listen_timeout: 3000,
    },

    // ============================================================
    // 3. WHATSAPP WATCHER
    // Monitors WhatsApp Web (Playwright session)
    // Requires: WhatsApp login completed via whatsapp_login.py
    // ============================================================
    {
      name: 'zoya-whatsapp',
      script: 'uv',
      args: 'run zoya-whatsapp',
      cwd: projectDir,
      instances: 1,
      exec_mode: 'fork',

      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      max_memory_restart: '800M', // Playwright uses more memory

      out_file: path.join(projectDir, 'AI_Employee_Vault/Logs/pm2-whatsapp-out.log'),
      error_file: path.join(projectDir, 'AI_Employee_Vault/Logs/pm2-whatsapp-err.log'),
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',

      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1',
      },

      kill_timeout: 10000, // Longer timeout for Playwright shutdown
      listen_timeout: 5000,
    },

    // ============================================================
    // 4. ORCHESTRATOR
    // Main coordinator: claims files from queue, invokes Claude
    // Includes: Ralph self-monitor + Contact Linker
    // ============================================================
    {
      name: 'zoya-orchestrator',
      script: 'uv',
      args: 'run zoya-orchestrator',
      cwd: projectDir,
      instances: 1,
      exec_mode: 'fork',

      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      max_memory_restart: '600M',

      out_file: path.join(projectDir, 'AI_Employee_Vault/Logs/pm2-orchestrator-out.log'),
      error_file: path.join(projectDir, 'AI_Employee_Vault/Logs/pm2-orchestrator-err.log'),
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',

      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1',
      },

      kill_timeout: 5000,
      listen_timeout: 3000,
    },
  ],

  // ============================================================
  // GLOBAL PM2 SETTINGS
  // ============================================================

  // Log rotation
  pm2_file: path.join(projectDir, '.pm2/pm2.log'),

  // Watch mode (auto-reload on file changes) - disable for production
  watch: false,

  // Cluster mode (for load balancing) - disabled, we need single instances
  instances: 1,

  // Interpreter
  interpreter: '/usr/bin/env',

  // Merge logs from all instances
  merge_logs: false,
};
