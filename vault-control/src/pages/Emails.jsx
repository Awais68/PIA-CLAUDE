import { useState, useEffect } from 'react'
import { Send, Edit2, Trash2, Archive, Mail } from 'lucide-react'
import axios from 'axios'

const folders = ['Inbox', 'Needs_Action', 'Sent', 'Done']

export default function Emails() {
  const [selectedFolder, setSelectedFolder] = useState('Needs_Action')
  const [emails, setEmails] = useState([])
  const [selectedEmail, setSelectedEmail] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchEmails()
  }, [])

  const fetchEmails = async () => {
    setLoading(true)
    try {
      const res = await axios.get('/api/emails')
      setEmails(res.data)
    } catch (err) {
      console.error('Failed to fetch emails:', err)
    } finally {
      setLoading(false)
    }
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'dark:bg-red-500/20 dark:text-red-400 bg-red-50 text-red-700'
      case 'medium': return 'dark:bg-yellow-500/20 dark:text-yellow-400 bg-yellow-50 text-yellow-700'
      case 'low': return 'dark:bg-green-500/20 dark:text-green-400 bg-green-50 text-green-700'
      default: return 'dark:bg-gray-500/20 dark:text-gray-400 bg-gray-50 text-gray-700'
    }
  }

  const stats = {
    total: emails.length,
    pending: emails.filter(e => e.priority === 'high').length,
    sentToday: 3,
    rejected: 1,
  }

  return (
    <div className="grid grid-cols-4 gap-4 h-full">
      {/* Left: Folders */}
      <div className="col-span-1 space-y-2">
        <h3 className="text-sm font-bold dark:text-[#E0E0E6] text-gray-900 px-4 py-2">FOLDERS</h3>
        {folders.map(folder => (
          <button
            key={folder}
            onClick={() => setSelectedFolder(folder)}
            className={`
              w-full text-left px-4 py-2 rounded transition-colors
              ${selectedFolder === folder
                ? 'dark:bg-[#00FF88]/10 dark:text-[#00FF88] bg-blue-50 text-blue-600'
                : 'dark:text-[#7A7A85] text-gray-600 hover:dark:bg-[#1A1A24] hover:bg-gray-50'
              }
            `}
          >
            {folder}
          </button>
        ))}

        {/* Stats */}
        <div className="mt-6 pt-6 border-t dark:border-[#1A1A24] border-gray-200 space-y-2 text-xs">
          <div className="flex justify-between px-4">
            <span className="dark:text-[#7A7A85] text-gray-500">Total</span>
            <span className="font-bold">{stats.total}</span>
          </div>
          <div className="flex justify-between px-4">
            <span className="dark:text-[#7A7A85] text-gray-500">Pending</span>
            <span className="font-bold text-red-500">{stats.pending}</span>
          </div>
          <div className="flex justify-between px-4">
            <span className="dark:text-[#7A7A85] text-gray-500">Sent Today</span>
            <span className="font-bold">{stats.sentToday}</span>
          </div>
          <div className="flex justify-between px-4">
            <span className="dark:text-[#7A7A85] text-gray-500">Rejected</span>
            <span className="font-bold">{stats.rejected}</span>
          </div>
        </div>
      </div>

      {/* Middle: Email List */}
      <div className="col-span-1 border-r dark:border-[#1A1A24] border-gray-200 overflow-y-auto">
        <h3 className="text-sm font-bold dark:text-[#E0E0E6] text-gray-900 px-4 py-2 sticky top-0 dark:bg-[#12121A] bg-white">
          {selectedFolder}
        </h3>
        {loading ? (
          <div className="flex justify-center py-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 dark:border-[#00FF88] border-blue-500" />
          </div>
        ) : (
          emails.map(email => (
            <div
              key={email.id}
              onClick={() => setSelectedEmail(email)}
              className={`
                px-4 py-3 border-b dark:border-[#1A1A24] border-gray-100 cursor-pointer transition-colors
                ${selectedEmail?.id === email.id
                  ? 'dark:bg-[#00FF88]/10 bg-blue-50'
                  : 'hover:dark:bg-[#1A1A24] hover:bg-gray-50'
                }
              `}
            >
              <div className="flex items-start justify-between gap-2 mb-1">
                <p className="font-semibold dark:text-[#E0E0E6] text-gray-900 text-sm truncate">
                  {email.from}
                </p>
                <span className={`badge text-xs ${getPriorityColor(email.priority)}`}>
                  {email.priority}
                </span>
              </div>
              <p className="text-sm dark:text-[#7A7A85] text-gray-600 truncate">
                {email.subject}
              </p>
              <p className="text-xs dark:text-[#7A7A85] text-gray-500 mt-1">
                {new Date(email.time).toLocaleDateString()}
              </p>
            </div>
          ))
        )}
      </div>

      {/* Right: Email Preview */}
      <div className="col-span-2 card flex flex-col">
        {selectedEmail ? (
          <>
            <div className="p-6 border-b dark:border-[#1A1A24] border-gray-200 flex-1 overflow-y-auto">
              <div className="mb-6">
                <p className="text-xs dark:text-[#7A7A85] text-gray-500 mb-2">FROM</p>
                <p className="font-semibold dark:text-[#E0E0E6] text-gray-900">
                  {selectedEmail.from}
                </p>
              </div>

              <div className="mb-6">
                <p className="text-xs dark:text-[#7A7A85] text-gray-500 mb-2">SUBJECT</p>
                <p className="text-lg font-bold dark:text-[#E0E0E6] text-gray-900">
                  {selectedEmail.subject}
                </p>
              </div>

              <div>
                <p className="text-xs dark:text-[#7A7A85] text-gray-500 mb-3">MESSAGE</p>
                <p className="dark:text-[#E0E0E6] text-gray-900 whitespace-pre-wrap">
                  {selectedEmail.preview || 'Email content...'}
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="p-4 flex gap-2">
              <button className="flex items-center gap-2 flex-1 px-3 py-2 rounded font-medium text-sm dark:bg-green-500/20 dark:text-green-400 bg-green-50 text-green-700 hover:dark:bg-green-500/30">
                <Send size={16} />
                Approve & Send
              </button>
              <button className="flex items-center gap-2 px-3 py-2 rounded font-medium text-sm dark:bg-blue-500/20 dark:text-blue-400 bg-blue-50 text-blue-700 hover:dark:bg-blue-500/30">
                <Edit2 size={16} />
              </button>
              <button className="flex items-center gap-2 px-3 py-2 rounded font-medium text-sm dark:bg-red-500/20 dark:text-red-400 bg-red-50 text-red-700 hover:dark:bg-red-500/30">
                <Trash2 size={16} />
              </button>
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Mail size={48} className="mx-auto dark:text-[#7A7A85] text-gray-400 mb-3" />
              <p className="dark:text-[#7A7A85] text-gray-500">Select an email</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
