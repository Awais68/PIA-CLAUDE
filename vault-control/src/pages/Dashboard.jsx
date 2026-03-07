import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, MessageSquare, Users, Mail, Linkedin, Twitter, Facebook, Instagram, AlertCircle, CheckCircle, Activity } from 'lucide-react'
import { BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { LineChart as MuiLineChart } from '@mui/x-charts'
import StatusIndicator from '../components/StatusIndicator'
import axios from 'axios'

const platforms = [
  { name: 'WhatsApp', icon: MessageSquare, color: '#25D366', incoming: 24, outgoing: 18, trend: 'up' },
  { name: 'LinkedIn', icon: Linkedin, color: '#0A66C2', incoming: 45, outgoing: 12, trend: 'up' },
  { name: 'Facebook', icon: Facebook, color: '#1877F2', incoming: 18, outgoing: 5, trend: 'down' },
  { name: 'Instagram', icon: Instagram, color: '#E4405F', incoming: 67, outgoing: 23, trend: 'up' },
  { name: 'Gmail', icon: Mail, color: '#EA4335', incoming: 156, outgoing: 89, trend: 'stable' },
  { name: 'Twitter', icon: Twitter, color: '#1DA1F2', incoming: 34, outgoing: 7, trend: 'up' },
]

const mockChartData = [
  { date: 'Mon', gmail: 32, whatsapp: 12, linkedin: 8, twitter: 5 },
  { date: 'Tue', gmail: 45, whatsapp: 18, linkedin: 12, twitter: 8 },
  { date: 'Wed', gmail: 38, whatsapp: 22, linkedin: 15, twitter: 6 },
  { date: 'Thu', gmail: 52, whatsapp: 25, linkedin: 18, twitter: 12 },
  { date: 'Fri', gmail: 48, whatsapp: 20, linkedin: 22, twitter: 9 },
  { date: 'Sat', gmail: 28, whatsapp: 15, linkedin: 5, twitter: 4 },
  { date: 'Sun', gmail: 19, whatsapp: 10, linkedin: 3, twitter: 2 },
]

const mockBarData = [
  { name: 'Gmail', value: 156, fill: '#EA4335' },
  { name: 'Instagram', value: 67, fill: '#E4405F' },
  { name: 'LinkedIn', value: 45, fill: '#0A66C2' },
  { name: 'WhatsApp', value: 24, fill: '#25D366' },
  { name: 'Twitter', value: 34, fill: '#1DA1F2' },
  { name: 'Facebook', value: 18, fill: '#1877F2' },
]

const mockActionData = [
  { day: 'Today', actions: 24 },
  { day: 'Yesterday', actions: 18 },
]

const services = [
  { name: 'Gmail Watcher', status: 'running', uptime: '4h 23m', lastActivity: '2 min ago' },
  { name: 'WhatsApp Watcher', status: 'running', uptime: '4h 23m', lastActivity: '5 min ago' },
  { name: 'LinkedIn Watcher', status: 'warning', uptime: '1h 12m', lastActivity: '45 min ago' },
  { name: 'Cloud VM', status: 'offline', uptime: null, lastActivity: null },
  { name: 'Odoo MCP', status: 'running', uptime: '4h 23m', lastActivity: '12 min ago' },
  { name: 'Email MCP', status: 'running', uptime: '4h 23m', lastActivity: '8 min ago' },
  { name: 'Social MCP', status: 'running', uptime: '4h 23m', lastActivity: '3 min ago' },
]

// Pokémon-style stat bar component
function StatBar({ label, value, maxValue = 100, color }) {
  const percentage = (value / maxValue) * 100
  return (
    <div className="mb-3">
      <div className="flex justify-between items-center mb-1">
        <span className="text-xs font-semibold dark:text-[#B0C4FF] text-gray-700 uppercase tracking-wide">{label}</span>
        <span className="text-xs font-bold dark:text-[#00FF88] text-blue-600">{value}</span>
      </div>
      <div className="w-full bg-gray-300 dark:bg-[#2A3E5F] rounded-full h-3 overflow-hidden border dark:border-[#3A5E7F] border-gray-400">
        <div
          className="h-full rounded-full transition-all duration-500 shadow-lg"
          style={{
            width: `${percentage}%`,
            background: `linear-gradient(90deg, ${color} 0%, ${color}dd 100%)`,
            boxShadow: `0 0 8px ${color}80`,
          }}
        />
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, healthRes] = await Promise.all([
          axios.get('/api/system/stats'),
          axios.get('/api/system/health'),
        ])
        setStats(statsRes.data)
        setHealth(healthRes.data)
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const getTrendIcon = (trend) => {
    if (trend === 'up') return <TrendingUp size={16} className="text-green-500" />
    if (trend === 'down') return <TrendingDown size={16} className="text-red-500" />
    return null
  }

  return (
    <div className="space-y-6">
      {/* PLATFORM ACTIVITY - TOP */}
      <div className="card p-6">
        <h2 className="text-lg font-bold dark:text-[#E0E0E6] text-gray-900 mb-6 font-mono">
          🌐 PLATFORM ACTIVITY
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {platforms.map(platform => {
            const Icon = platform.icon
            const maxActivity = Math.max(platform.incoming, platform.outgoing)
            return (
              <div key={platform.name} className="p-4 rounded-lg dark:bg-[#0F1A2E] bg-gray-50 hover:dark:bg-[#1B2A48] hover:bg-gray-100 transition-all border dark:border-[#2A3E5F] border-gray-200">
                <div className="flex items-center gap-2 mb-4">
                  <Icon size={22} style={{ color: platform.color }} />
                  <div>
                    <h3 className="font-semibold dark:text-[#E0E0E6] text-gray-900 text-sm">
                      {platform.name}
                    </h3>
                    <span className="text-xs font-semibold dark:text-[#00FF88] text-green-600">
                      {platform.trend === 'up' ? '↑ Up' : platform.trend === 'down' ? '↓ Down' : '→ Stable'}
                    </span>
                  </div>
                </div>

                {/* Pokémon-style stats */}
                <StatBar label="Incoming" value={platform.incoming} maxValue={160} color={platform.color} />
                <StatBar label="Outgoing" value={platform.outgoing} maxValue={90} color={platform.color} />
              </div>
            )
          })}
        </div>
      </div>

      {/* CHARTS SECTION - MUI X Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* MUI Line Chart - Messages */}
        <div className="card p-6">
          <h2 className="text-lg font-bold dark:text-[#E0E0E6] text-gray-900 mb-4 font-mono">
            📈 MESSAGES (7 DAYS)
          </h2>
          <div className="w-full flex justify-center bg-gradient-to-br dark:from-[#1B2A48] dark:to-[#0F1A2E] rounded-lg p-4">
            <MuiLineChart
              xAxis={[{ data: [1, 2, 3, 4, 5, 6, 7], label: 'Days' }]}
              series={[
                { data: [32, 45, 38, 52, 48, 28, 19], label: 'Gmail', color: '#EA4335', curve: 'natural' },
                { data: [12, 18, 22, 25, 20, 15, 10], label: 'WhatsApp', color: '#25D366', curve: 'natural' },
                { data: [8, 12, 15, 18, 22, 5, 3], label: 'LinkedIn', color: '#0A66C2', curve: 'natural' },
                { data: [5, 8, 6, 12, 9, 4, 2], label: 'Twitter', color: '#1DA1F2', curve: 'natural' },
              ]}
              width={450}
              height={280}
              slotProps={{
                legend: { position: { vertical: 'bottom', horizontal: 'middle' } },
              }}
              sx={{
                '& .MuiChartsAxis-bottom .MuiChartsAxis-tickContainer': { color: '#B0C4FF' },
                '& .MuiChartsAxis-left .MuiChartsAxis-tickContainer': { color: '#B0C4FF' },
              }}
            />
          </div>
        </div>

        {/* Bar Chart - Top Platforms */}
        <div className="card p-6">
          <h2 className="text-lg font-bold dark:text-[#E0E0E6] text-gray-900 mb-4 font-mono">
            📊 TOP PLATFORMS (INCOMING)
          </h2>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart
              data={mockBarData}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 80, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis type="number" stroke="#7A7A85" style={{ fontSize: '12px' }} />
              <YAxis dataKey="name" type="category" stroke="#7A7A85" style={{ fontSize: '12px' }} width={70} />
              <Tooltip
                contentStyle={{ background: '#1B2A48', border: '1px solid #2A3E5F', borderRadius: '8px' }}
              />
              <Bar dataKey="value" radius={[0, 8, 8, 0]}>
                {mockBarData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ACTIONS EXECUTED - FUNNEL STYLE */}
      <div className="card p-6">
        <h2 className="text-lg font-bold dark:text-[#E0E0E6] text-gray-900 mb-4 font-mono">
          ✅ ACTIONS EXECUTED (FUNNEL)
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart
            data={[
              { stage: 'Initiated', value: 24, fill: '#00FF88' },
              { stage: 'Approved', value: 18, fill: '#00D966' },
              { stage: 'Processing', value: 12, fill: '#00B050' },
              { stage: 'Completed', value: 8, fill: '#008800' },
            ]}
            layout="vertical"
            margin={{ top: 20, right: 30, left: 100, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis type="number" stroke="#B0C4FF" />
            <YAxis dataKey="stage" type="category" stroke="#B0C4FF" width={100} />
            <Tooltip
              contentStyle={{
                background: '#0F1A2E',
                border: '1px solid #2A3E5F',
                borderRadius: '8px',
                color: '#E0E0E6',
              }}
              cursor={{ fill: 'rgba(0,255,136,0.1)' }}
            />
            <Bar dataKey="value" fill="#00FF88" radius={[0, 8, 8, 0]}>
              {[
                { stage: 'Initiated', value: 24, fill: '#00FF88' },
                { stage: 'Approved', value: 18, fill: '#00D966' },
                { stage: 'Processing', value: 12, fill: '#00B050' },
                { stage: 'Completed', value: 8, fill: '#008800' },
              ].map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* SYSTEM STATUS - BOTTOM LINE */}
      <div className="card p-6">
        <h2 className="text-lg font-bold dark:text-[#E0E0E6] text-gray-900 mb-4 font-mono">
          🔧 SYSTEM STATUS
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {services.map(service => {
            const isRunning = service.status === 'running'
            const isWarning = service.status === 'warning'
            const isOffline = service.status === 'offline'

            return (
              <div
                key={service.name}
                className={`p-4 rounded-lg border transition-all ${
                  isRunning
                    ? 'dark:bg-gradient-to-br dark:from-[#1B2A48] dark:to-[#0F1A2E] dark:border-[#00FF88]/30 bg-green-50 border-green-200'
                    : isWarning
                    ? 'dark:bg-gradient-to-br dark:from-[#2A2A1A] dark:to-[#1A1A0F] dark:border-[#FFB800]/30 bg-yellow-50 border-yellow-200'
                    : 'dark:bg-gradient-to-br dark:from-[#2A1A1A] dark:to-[#1A0F0F] dark:border-[#FF4444]/30 bg-red-50 border-red-200'
                }`}
              >
                <div className="flex items-start gap-3 mb-3">
                  <div className={`w-3 h-3 rounded-full mt-1 ${
                    isRunning ? 'bg-green-500 animate-pulse' : isWarning ? 'bg-yellow-500 animate-pulse' : 'bg-red-500'
                  }`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold dark:text-[#E0E0E6] text-gray-900 truncate">
                      {service.name}
                    </p>
                    <p className={`text-xs font-bold mt-1 ${
                      isRunning
                        ? 'dark:text-[#00FF88] text-green-600'
                        : isWarning
                        ? 'dark:text-[#FFB800] text-yellow-600'
                        : 'dark:text-[#FF4444] text-red-600'
                    }`}>
                      {service.status.toUpperCase()}
                    </p>
                  </div>
                </div>

                {service.uptime && (
                  <div className="space-y-2 text-xs dark:text-[#B0C4FF] text-gray-600">
                    <div className="flex justify-between">
                      <span>Uptime:</span>
                      <span className="font-semibold">{service.uptime}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Active:</span>
                      <span className="font-semibold">{service.lastActivity}</span>
                    </div>
                  </div>
                )}

                {!service.uptime && (
                  <div className="text-xs dark:text-[#B0C4FF] text-gray-600">
                    <p className="italic">Service offline</p>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* PENDING ACTIONS */}
      <div className="card p-6 bg-gradient-to-r dark:from-[#00FF88]/5 dark:to-[#1DA1F2]/5 from-green-50 to-blue-50 border dark:border-[#00FF88]/20 border-blue-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm dark:text-[#B0C4FF] text-gray-600 font-mono">⚡ PENDING ACTIONS</p>
            <p className="text-4xl font-bold dark:text-[#00FF88] text-green-600 mt-2">18</p>
          </div>
          <div className="text-right">
            <p className="text-xs dark:text-[#B0C4FF] text-gray-500">Requires review</p>
            <button className="mt-3 px-4 py-2 rounded-lg font-medium dark:bg-[#00FF88] dark:text-[#0F1A2E] bg-blue-500 text-white hover:opacity-90 transition-all">
              Review Now
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
