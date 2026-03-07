import { useState } from 'react'
import { Send, Save, Upload, Calendar, Sparkles, Copy, Check } from 'lucide-react'
import axios from 'axios'

const platforms = [
  { id: 'linkedin', name: 'LinkedIn', limit: 3000, color: '#0A66C2' },
  { id: 'facebook', name: 'Facebook', limit: 63206, color: '#1877F2' },
  { id: 'instagram', name: 'Instagram', limit: 2200, color: '#E4405F' },
  { id: 'twitter', name: 'Twitter', limit: 280, color: '#1DA1F2' },
]

const mockQueue = [
  { id: 1, preview: 'Excited to announce our Q1 launch...', platforms: ['linkedin', 'twitter'], status: 'QUEUED', date: '2024-03-06' },
  { id: 2, preview: 'Team highlights from this week...', platforms: ['facebook', 'instagram'], status: 'APPROVED', date: '2024-03-07 14:00' },
]

const mockHistory = [
  { id: 1, preview: 'February recap post', platforms: ['linkedin'], date: '2024-02-28', status: 'POSTED', engagement: 245 },
  { id: 2, preview: 'New blog announcement', platforms: ['twitter'], date: '2024-02-25', status: 'POSTED', engagement: 89 },
]

export default function SocialMedia() {
  const [content, setContent] = useState('')
  const [selectedPlatforms, setSelectedPlatforms] = useState(['linkedin', 'twitter'])
  const [scheduleTime, setScheduleTime] = useState('')
  const [showSchedule, setShowSchedule] = useState(false)
  const [activeTab, setActiveTab] = useState('compose')
  const [topic, setTopic] = useState('')
  const [generatedPosts, setGeneratedPosts] = useState({
    twitter: [],
    linkedin: [],
    facebook: '',
    instagram: '',
  })
  const [isGenerating, setIsGenerating] = useState(false)
  const [copiedId, setCopiedId] = useState(null)

  const charCount = (platform) => {
    const p = platforms.find(x => x.id === platform)
    return { current: content.length, max: p.limit }
  }

  const isOverLimit = (platform) => {
    const { current, max } = charCount(platform)
    return current > max
  }

  const togglePlatform = (id) => {
    setSelectedPlatforms(prev => 
      prev.includes(id) 
        ? prev.filter(x => x !== id)
        : [...prev, id]
    )
  }

  const handlePost = async () => {
    if (!content.trim()) return
    
    try {
      await axios.post('/api/social/post', {
        content,
        platforms: selectedPlatforms,
        scheduleTime: scheduleTime || null,
      })
      setContent('')
      setScheduleTime('')
    } catch (err) {
      console.error('Failed to create post:', err)
    }
  }

  const handleSaveDraft = async () => {
    try {
      await axios.post('/api/social/draft', {
        content,
        platforms: selectedPlatforms,
        title: content.substring(0, 50),
      })
      setContent('')
    } catch (err) {
      console.error('Failed to save draft:', err)
    }
  }

  const generatePosts = async () => {
    if (!topic.trim()) return

    setIsGenerating(true)
    try {
      const response = await axios.post('/api/social/generate', {
        topic: topic,
      })

      // Mock response if API not available
      if (response.data) {
        setGeneratedPosts(response.data)
      } else {
        setGeneratedPosts({
          twitter: [
            `🚀 Exciting news about ${topic}! Just launched our latest initiative. The future is here! #innovation`,
            `Did you know? ${topic} is transforming the industry. Join us on this amazing journey! 🌟`,
            `Breaking: We're revolutionizing ${topic}. Stay tuned for more updates! 💡 #tech`,
          ],
          linkedin: [
            `We're thrilled to announce our new approach to ${topic}. This represents a significant milestone in our journey to deliver exceptional value to our stakeholders. Our team has worked tirelessly to bring this innovation to market, and we believe it will redefine standards in the industry. Learn more about what this means for the future.`,
            `${topic} is at the heart of everything we do. Today, we're sharing our vision for how this will shape the next decade of growth and innovation. We're grateful for the support of our amazing community and partners who believe in this mission.`,
          ],
          facebook: `🎉 Big news! We're excited to share our latest development in ${topic}. This is something we've been working on for months, and we can't wait for you to experience it. Check out the full story and let us know what you think! Your feedback means the world to us.`,
          instagram: `✨ The future of ${topic} starts now ✨\n\nWe're thrilled to unveil what we've been building. #innovation #future #${topic.replace(/\\s+/g, '')}`,
        })
      }
    } catch (err) {
      console.error('Failed to generate posts:', err)
      // Fallback mock data
      setGeneratedPosts({
        twitter: [
          `🚀 Exciting news about ${topic}! Just launched our latest initiative. The future is here! #innovation`,
          `Did you know? ${topic} is transforming the industry. Join us on this amazing journey! 🌟`,
          `Breaking: We're revolutionizing ${topic}. Stay tuned for more updates! 💡 #tech`,
        ],
        linkedin: [
          `We're thrilled to announce our new approach to ${topic}. This represents a significant milestone in our journey to deliver exceptional value to our stakeholders.`,
          `${topic} is at the heart of everything we do. Today, we're sharing our vision for how this will shape the next decade of growth and innovation.`,
        ],
        facebook: `🎉 Big news! We're excited to share our latest development in ${topic}.`,
        instagram: `✨ The future of ${topic} starts now ✨\n\n#innovation #future`,
      })
    } finally {
      setIsGenerating(false)
    }
  }

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  return (
    <div className="space-y-6">
      {/* Tabs */}
      <div className="flex gap-4 border-b dark:border-[#1A1A24] border-gray-200 overflow-x-auto">
        <button
          onClick={() => setActiveTab('generate')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-all whitespace-nowrap flex items-center gap-2 ${
            activeTab === 'generate'
              ? 'dark:border-[#00FF88] dark:text-[#00FF88] border-blue-500 text-blue-600'
              : 'dark:border-transparent dark:text-[#7A7A85] border-transparent text-gray-500'
          }`}
        >
          <Sparkles size={16} />
          Generate
        </button>
        <button
          onClick={() => setActiveTab('compose')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-all ${
            activeTab === 'compose'
              ? 'dark:border-[#00FF88] dark:text-[#00FF88] border-blue-500 text-blue-600'
              : 'dark:border-transparent dark:text-[#7A7A85] border-transparent text-gray-500'
          }`}
        >
          Compose
        </button>
        <button
          onClick={() => setActiveTab('queue')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-all ${
            activeTab === 'queue'
              ? 'dark:border-[#00FF88] dark:text-[#00FF88] border-blue-500 text-blue-600'
              : 'dark:border-transparent dark:text-[#7A7A85] border-transparent text-gray-500'
          }`}
        >
          Queue
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-4 py-3 font-medium text-sm border-b-2 transition-all ${
            activeTab === 'history'
              ? 'dark:border-[#00FF88] dark:text-[#00FF88] border-blue-500 text-blue-600'
              : 'dark:border-transparent dark:text-[#7A7A85] border-transparent text-gray-500'
          }`}
        >
          History
        </button>
      </div>

      {/* Generate Tab */}
      {activeTab === 'generate' && (
        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-bold dark:text-[#E0E0E6] text-gray-900 mb-4 font-mono flex items-center gap-2">
              <Sparkles size={20} className="dark:text-[#00FF88] text-blue-500" />
              AI CONTENT GENERATOR
            </h2>

            <p className="dark:text-[#7A7A85] text-gray-600 text-sm mb-4">
              Enter a topic and Claude will generate optimized posts for all platforms:
            </p>
            <ul className="dark:text-[#7A7A85] text-gray-600 text-sm mb-6 space-y-1 ml-4 list-disc">
              <li>3 Twitter posts (engaging & concise)</li>
              <li>2 LinkedIn posts (professional & detailed)</li>
              <li>1 Facebook post (community-focused)</li>
              <li>1 Instagram post (visual & trendy)</li>
            </ul>

            <div className="flex gap-3 mb-6">
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !isGenerating && generatePosts()}
                placeholder="Enter a topic (e.g., 'New product launch', 'Company milestone')"
                className="flex-1 px-4 py-3 rounded-lg dark:bg-[#1A1A24] dark:text-[#E0E0E6] bg-gray-50 text-gray-900 placeholder-gray-500 dark:placeholder-[#7A7A85]"
              />
              <button
                onClick={generatePosts}
                disabled={isGenerating || !topic.trim()}
                className="flex items-center gap-2 px-6 py-3 rounded-lg font-medium dark:bg-[#00FF88] dark:text-[#0A0A0F] bg-blue-500 text-white hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Sparkles size={18} />
                {isGenerating ? 'Generating...' : 'Generate'}
              </button>
            </div>
          </div>

          {/* Generated Posts */}
          {(generatedPosts.twitter.length > 0 || generatedPosts.linkedin.length > 0) && (
            <div className="space-y-6">
              {/* Twitter Posts */}
              <div className="space-y-3">
                <h3 className="text-lg font-bold dark:text-[#1DA1F2] text-blue-600 font-mono">
                  Twitter Posts (3)
                </h3>
                {generatedPosts.twitter.map((post, idx) => (
                  <div key={`twitter-${idx}`} className="card p-4 bg-gradient-to-r dark:from-[#1DA1F2]/10 dark:to-transparent from-blue-50 to-transparent">
                    <div className="flex gap-4">
                      <div className="flex-1">
                        <p className="dark:text-[#E0E0E6] text-gray-900 text-sm mb-2">{post}</p>
                        <p className="text-xs dark:text-[#7A7A85] text-gray-500">{post.length}/280 chars</p>
                      </div>
                      <button
                        onClick={() => copyToClipboard(post, `twitter-${idx}`)}
                        className="flex-shrink-0 p-2 rounded dark:bg-[#1A1A24] dark:text-[#7A7A85] dark:hover:text-[#00FF88] bg-gray-100 text-gray-600 hover:text-blue-600 transition-colors"
                      >
                        {copiedId === `twitter-${idx}` ? <Check size={18} /> : <Copy size={18} />}
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* LinkedIn Posts */}
              <div className="space-y-3">
                <h3 className="text-lg font-bold dark:text-[#0A66C2] text-blue-700 font-mono">
                  LinkedIn Posts (2)
                </h3>
                {generatedPosts.linkedin.map((post, idx) => (
                  <div key={`linkedin-${idx}`} className="card p-4 bg-gradient-to-r dark:from-[#0A66C2]/10 dark:to-transparent from-blue-50 to-transparent">
                    <div className="flex gap-4">
                      <div className="flex-1">
                        <p className="dark:text-[#E0E0E6] text-gray-900 text-sm mb-2">{post}</p>
                        <p className="text-xs dark:text-[#7A7A85] text-gray-500">{post.length}/3000 chars</p>
                      </div>
                      <button
                        onClick={() => copyToClipboard(post, `linkedin-${idx}`)}
                        className="flex-shrink-0 p-2 rounded dark:bg-[#1A1A24] dark:text-[#7A7A85] dark:hover:text-[#00FF88] bg-gray-100 text-gray-600 hover:text-blue-600 transition-colors"
                      >
                        {copiedId === `linkedin-${idx}` ? <Check size={18} /> : <Copy size={18} />}
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Facebook Post */}
              {generatedPosts.facebook && (
                <div className="space-y-3">
                  <h3 className="text-lg font-bold dark:text-[#1877F2] text-blue-600 font-mono">
                    Facebook Post (1)
                  </h3>
                  <div className="card p-4 bg-gradient-to-r dark:from-[#1877F2]/10 dark:to-transparent from-blue-50 to-transparent">
                    <div className="flex gap-4">
                      <div className="flex-1">
                        <p className="dark:text-[#E0E0E6] text-gray-900 text-sm mb-2 whitespace-pre-wrap">
                          {generatedPosts.facebook}
                        </p>
                      </div>
                      <button
                        onClick={() => copyToClipboard(generatedPosts.facebook, 'facebook')}
                        className="flex-shrink-0 p-2 rounded dark:bg-[#1A1A24] dark:text-[#7A7A85] dark:hover:text-[#00FF88] bg-gray-100 text-gray-600 hover:text-blue-600 transition-colors"
                      >
                        {copiedId === 'facebook' ? <Check size={18} /> : <Copy size={18} />}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Instagram Post */}
              {generatedPosts.instagram && (
                <div className="space-y-3">
                  <h3 className="text-lg font-bold dark:text-[#E4405F] text-pink-600 font-mono">
                    Instagram Post (1)
                  </h3>
                  <div className="card p-4 bg-gradient-to-r dark:from-[#E4405F]/10 dark:to-transparent from-pink-50 to-transparent">
                    <div className="flex gap-4">
                      <div className="flex-1">
                        <p className="dark:text-[#E0E0E6] text-gray-900 text-sm mb-2 whitespace-pre-wrap">
                          {generatedPosts.instagram}
                        </p>
                      </div>
                      <button
                        onClick={() => copyToClipboard(generatedPosts.instagram, 'instagram')}
                        className="flex-shrink-0 p-2 rounded dark:bg-[#1A1A24] dark:text-[#7A7A85] dark:hover:text-[#00FF88] bg-gray-100 text-gray-600 hover:text-blue-600 transition-colors"
                      >
                        {copiedId === 'instagram' ? <Check size={18} /> : <Copy size={18} />}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Use Generated Posts */}
              <div className="card p-4 bg-gradient-to-r dark:from-[#00FF88]/10 dark:to-transparent from-green-50 to-transparent">
                <p className="dark:text-[#7A7A85] text-gray-600 text-sm mb-3">
                  💡 Pro tip: Copy any post above and use the Compose tab to schedule or post directly!
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Compose Tab */}
      {activeTab === 'compose' && (
        <div className="space-y-6">
          {/* Compose Box */}
          <div className="card p-6">
            <h2 className="text-lg font-bold dark:text-[#E0E0E6] text-gray-900 mb-4 font-mono">
              NEW POST
            </h2>
            
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="What's on your mind? Share with your audience..."
              className="w-full px-4 py-3 rounded-lg dark:bg-[#1A1A24] dark:text-[#E0E0E6] bg-gray-50 text-gray-900 resize-none mb-4"
              rows={6}
            />

            {/* Character Limits */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              {platforms.map(p => {
                const over = isOverLimit(p.id) && selectedPlatforms.includes(p.id)
                return (
                  <div key={p.id} className="text-center">
                    <p className="text-xs font-semibold dark:text-[#7A7A85] text-gray-600 mb-2">
                      {p.name}
                    </p>
                    <div className={`
                      px-3 py-2 rounded text-sm font-mono
                      ${over 
                        ? 'dark:bg-red-500/20 dark:text-red-400 bg-red-50 text-red-600' 
                        : 'dark:bg-[#1A1A24] dark:text-[#00FF88] bg-gray-100 text-blue-600'
                      }
                    `}>
                      {content.length}/{p.limit}
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Platform Selection */}
            <div className="mb-6">
              <p className="text-sm font-semibold dark:text-[#E0E0E6] text-gray-900 mb-3">
                Post to:
              </p>
              <div className="flex gap-3">
                {platforms.map(p => (
                  <button
                    key={p.id}
                    onClick={() => togglePlatform(p.id)}
                    className={`
                      px-4 py-2 rounded font-medium text-sm transition-all
                      ${selectedPlatforms.includes(p.id)
                        ? `text-white`
                        : 'dark:bg-[#1A1A24] dark:text-[#7A7A85] bg-gray-100 text-gray-600'
                      }
                    `}
                    style={selectedPlatforms.includes(p.id) ? { background: p.color } : {}}
                  >
                    ✓ {p.name}
                  </button>
                ))}
              </div>
            </div>

            {/* Schedule Option */}
            <div className="mb-6 flex items-center gap-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showSchedule}
                  onChange={(e) => setShowSchedule(e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm dark:text-[#E0E0E6] text-gray-900">Schedule post</span>
              </label>
              {showSchedule && (
                <input
                  type="datetime-local"
                  value={scheduleTime}
                  onChange={(e) => setScheduleTime(e.target.value)}
                  className="px-3 py-1 rounded text-sm dark:bg-[#1A1A24] dark:text-[#E0E0E6] bg-gray-50"
                />
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                onClick={handlePost}
                className="flex items-center gap-2 flex-1 px-4 py-2 rounded font-medium dark:bg-[#00FF88] dark:text-[#0A0A0F] bg-blue-500 text-white hover:opacity-90"
              >
                <Send size={18} />
                Send to Approval
              </button>
              <button
                onClick={handleSaveDraft}
                className="flex items-center gap-2 px-4 py-2 rounded font-medium dark:bg-[#1A1A24] dark:text-[#00FF88] bg-gray-100 text-gray-900 hover:dark:bg-[#00FF88]/10"
              >
                <Save size={18} />
                Save Draft
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Queue Tab */}
      {activeTab === 'queue' && (
        <div className="space-y-4">
          {mockQueue.map(post => (
            <div key={post.id} className="card p-4">
              <div className="flex justify-between items-start gap-4">
                <div className="flex-1">
                  <p className="dark:text-[#E0E0E6] text-gray-900 mb-2">
                    {post.preview}
                  </p>
                  <div className="flex gap-2 mb-3">
                    {post.platforms.map(p => (
                      <span key={p} className="text-xs px-2 py-1 rounded dark:bg-[#1A1A24] dark:text-[#7A7A85] bg-gray-100 text-gray-600">
                        {platforms.find(x => x.id === p)?.name}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="text-right">
                  <span className={`text-xs font-bold ${post.status === 'POSTED' ? 'text-green-500' : 'text-orange-500'}`}>
                    {post.status}
                  </span>
                  <p className="text-xs dark:text-[#7A7A85] text-gray-500 mt-1">{post.date}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div className="space-y-4">
          {mockHistory.map(post => (
            <div key={post.id} className="card p-4">
              <div className="flex justify-between items-start gap-4">
                <div className="flex-1">
                  <p className="dark:text-[#E0E0E6] text-gray-900 font-medium mb-2">
                    {post.preview}
                  </p>
                  <div className="flex gap-2">
                    {post.platforms.map(p => (
                      <span key={p} className="text-xs px-2 py-1 rounded dark:bg-[#1A1A24] dark:text-[#7A7A85] bg-gray-100 text-gray-600">
                        {platforms.find(x => x.id === p)?.name}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-xs font-bold text-green-500">{post.status}</span>
                  <p className="text-xs dark:text-[#7A7A85] text-gray-500 mt-1">{post.engagement} likes</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
