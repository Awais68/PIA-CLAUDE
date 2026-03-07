import { useState } from 'react'
import { RefreshCw, TrendingUp, AlertCircle } from 'lucide-react'

export default function Accounting() {
  const [selectedPeriod, setSelectedPeriod] = useState('month')

  const transactions = [
    { id: 1, date: '2024-03-05', desc: 'AWS Services', amount: 1250, type: 'expense', status: 'paid' },
    { id: 2, date: '2024-03-04', desc: 'Client Invoice #001', amount: 5000, type: 'income', status: 'paid' },
    { id: 3, date: '2024-03-03', desc: 'Team Salary', amount: 8000, type: 'expense', status: 'pending' },
    { id: 4, date: '2024-03-02', desc: 'License Renewal', amount: 299, type: 'expense', status: 'pending' },
    { id: 5, date: '2024-03-01', desc: 'Client Invoice #002', amount: 3500, type: 'income', status: 'paid' },
  ]

  const subscriptions = [
    { id: 1, name: 'Slack Pro', cost: 99, lastUsed: '2 days ago', action: 'Keep' },
    { id: 2, name: 'Unused Tool', cost: 49, lastUsed: '3 months ago', action: 'Cancel' },
    { id: 3, name: 'GitHub Enterprise', cost: 231, lastUsed: '1 hour ago', action: 'Keep' },
  ]

  const briefing = {
    title: 'CEO Briefing - March 2024',
    revenue: '$12,450',
    expenses: '$9,549',
    profit: '$2,901',
    bottlenecks: ['Payment processing delays', 'Team resource constraints'],
    suggestions: ['Automate invoice generation', 'Review subscription costs'],
  }

  return (
    <div className="space-y-6">
      {/* Odoo Connection Status */}
      <div className="card p-6 bg-gradient-to-r dark:from-green-500/10 dark:to-[#12121A] from-green-50 to-white border-l-4 dark:border-l-green-500 border-l-green-500">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-bold dark:text-[#E0E0E6] text-gray-900 mb-2">Odoo Server</h3>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm dark:text-green-400 text-green-600">Running</span>
              <span className="text-xs dark:text-[#7A7A85] text-gray-500 ml-4">Last sync: 2 min ago</span>
            </div>
          </div>
          <button className="flex items-center gap-2 px-4 py-2 rounded font-medium text-sm dark:bg-[#1A1A24] dark:text-[#00FF88] bg-gray-100 hover:dark:bg-[#00FF88]/10">
            <RefreshCw size={16} />
            Sync Now
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card p-4 text-center">
          <p className="text-xs dark:text-[#7A7A85] text-gray-500 mb-2">This Month Revenue</p>
          <p className="text-3xl font-bold dark:text-green-400 text-green-600">$12,450</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-xs dark:text-[#7A7A85] text-gray-500 mb-2">Total Expenses</p>
          <p className="text-3xl font-bold dark:text-red-400 text-red-600">$9,549</p>
        </div>
        <div className="card p-4 text-center">
          <p className="text-xs dark:text-[#7A7A85] text-gray-500 mb-2">Net Profit</p>
          <p className="text-3xl font-bold dark:text-[#00FF88] text-blue-600">$2,901</p>
        </div>
      </div>

      {/* Period Filter */}
      <div className="flex gap-2">
        {['week', 'month', 'quarter', 'year'].map(period => (
          <button
            key={period}
            onClick={() => setSelectedPeriod(period)}
            className={`px-4 py-2 rounded capitalize font-medium text-sm transition-all ${
              selectedPeriod === period
                ? 'dark:bg-[#00FF88] dark:text-[#0A0A0F] bg-blue-500 text-white'
                : 'dark:bg-[#1A1A24] dark:text-[#7A7A85] bg-gray-100 text-gray-600'
            }`}
          >
            {period}
          </button>
        ))}
      </div>

      {/* Transactions Table */}
      <div className="card overflow-hidden">
        <div className="p-4 border-b dark:border-[#1A1A24] border-gray-200">
          <h3 className="font-bold dark:text-[#E0E0E6] text-gray-900 font-mono">TRANSACTIONS</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b dark:border-[#1A1A24] border-gray-200">
                <th className="px-4 py-2 text-left dark:text-[#7A7A85] text-gray-500">Date</th>
                <th className="px-4 py-2 text-left dark:text-[#7A7A85] text-gray-500">Description</th>
                <th className="px-4 py-2 text-left dark:text-[#7A7A85] text-gray-500">Amount</th>
                <th className="px-4 py-2 text-left dark:text-[#7A7A85] text-gray-500">Status</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map(tx => (
                <tr key={tx.id} className="border-b dark:border-[#1A1A24] border-gray-100 hover:dark:bg-[#1A1A24] hover:bg-gray-50">
                  <td className="px-4 py-3 dark:text-[#7A7A85] text-gray-600">{tx.date}</td>
                  <td className="px-4 py-3 dark:text-[#E0E0E6] text-gray-900">{tx.desc}</td>
                  <td className={`px-4 py-3 font-semibold ${tx.type === 'income' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                    {tx.type === 'income' ? '+' : '-'}${tx.amount}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-1 rounded ${tx.status === 'paid' ? 'dark:bg-green-500/20 dark:text-green-400 bg-green-50 text-green-700' : 'dark:bg-yellow-500/20 dark:text-yellow-400 bg-yellow-50 text-yellow-700'}`}>
                      {tx.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* CEO Briefing */}
      <div className="card p-6 bg-gradient-to-r dark:from-purple-500/10 dark:to-[#12121A] from-purple-50 to-white border-l-4 dark:border-l-purple-500 border-l-purple-500">
        <div className="flex items-start justify-between mb-4">
          <h3 className="font-bold dark:text-[#E0E0E6] text-gray-900 text-lg">{briefing.title}</h3>
          <button className="px-3 py-1 rounded text-xs font-medium dark:bg-[#1A1A24] dark:text-[#00FF88] bg-gray-100">
            Regenerate
          </button>
        </div>
        
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div>
            <p className="text-xs dark:text-[#7A7A85] text-gray-500">Revenue</p>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">{briefing.revenue}</p>
          </div>
          <div>
            <p className="text-xs dark:text-[#7A7A85] text-gray-500">Expenses</p>
            <p className="text-2xl font-bold text-red-600 dark:text-red-400">{briefing.expenses}</p>
          </div>
          <div>
            <p className="text-xs dark:text-[#7A7A85] text-gray-500">Profit</p>
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{briefing.profit}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div>
            <h4 className="font-semibold dark:text-[#E0E0E6] text-gray-900 mb-3 flex items-center gap-2">
              <AlertCircle size={16} />
              Bottlenecks
            </h4>
            <ul className="space-y-1 text-sm dark:text-[#7A7A85] text-gray-600">
              {briefing.bottlenecks.map((b, i) => (
                <li key={i}>• {b}</li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="font-semibold dark:text-[#E0E0E6] text-gray-900 mb-3 flex items-center gap-2">
              <TrendingUp size={16} />
              Suggestions
            </h4>
            <ul className="space-y-1 text-sm dark:text-[#7A7A85] text-gray-600">
              {briefing.suggestions.map((s, i) => (
                <li key={i}>• {s}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Subscriptions Audit */}
      <div className="card p-6">
        <h3 className="font-bold dark:text-[#E0E0E6] text-gray-900 mb-4 font-mono">SUBSCRIPTION AUDIT</h3>
        <div className="space-y-3">
          {subscriptions.map(sub => (
            <div key={sub.id} className="flex items-center justify-between p-3 dark:bg-[#1A1A24] bg-gray-50 rounded">
              <div>
                <p className="font-semibold dark:text-[#E0E0E6] text-gray-900">{sub.name}</p>
                <p className="text-xs dark:text-[#7A7A85] text-gray-500">Last used: {sub.lastUsed}</p>
              </div>
              <div className="flex items-center gap-3">
                <p className="font-bold dark:text-red-400 text-red-600">${sub.cost}/mo</p>
                <button className="px-3 py-1 rounded text-sm font-medium dark:bg-green-500/20 dark:text-green-400 bg-green-50 text-green-700">
                  {sub.action}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
