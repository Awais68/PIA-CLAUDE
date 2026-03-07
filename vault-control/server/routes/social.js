import express from 'express'
import { readVaultFiles, getVaultPath, writeFile } from '../vault-reader.js'

const router = express.Router()

// GET all social data (drafts + history)
router.get('/', (req, res) => {
  const files = readVaultFiles('Drafts')
  const drafts = files.filter(f => f.frontmatter.type === 'post').map(file => ({
    id: file.id,
    ...file.frontmatter,
    preview: file.content.substring(0, 150),
  }))

  const posted = [
    {
      id: 'post-1',
      title: 'February Recap',
      date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      platforms: ['linkedin', 'twitter', 'facebook'],
      status: 'posted',
    },
  ]

  res.json({ drafts, posted })
})

// GET all social posts (drafts + queued)
router.get('/drafts', (req, res) => {
  const files = readVaultFiles('Drafts')
  const drafts = files.filter(f => f.frontmatter.type === 'post').map(file => ({
    id: file.id,
    ...file.frontmatter,
    preview: file.content.substring(0, 150),
  }))

  if (drafts.length === 0) {
    return res.json([
      {
        id: 'draft-1',
        title: 'Q1 Product Launch',
        content: 'Excited to announce our Q1 product launch! 🚀 New features include...',
        platforms: ['linkedin', 'twitter'],
        createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        status: 'draft',
      },
      {
        id: 'draft-2',
        title: 'Team Highlights',
        content: 'This week our team achieved some amazing milestones...',
        platforms: ['facebook', 'instagram'],
        createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        status: 'draft',
      },
    ])
  }

  res.json(drafts)
})

// GET posted history
router.get('/history', (req, res) => {
  const posted = [
    {
      id: 'post-1',
      title: 'February Recap',
      date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      platforms: ['linkedin', 'twitter', 'facebook'],
      status: 'posted',
      engagement: {
        linkedin: { likes: 245, comments: 18 },
        twitter: { retweets: 89, likes: 342 },
        facebook: { likes: 156, shares: 12 },
      },
    },
    {
      id: 'post-2',
      title: 'New Blog Post',
      date: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
      platforms: ['linkedin'],
      status: 'posted',
      engagement: {
        linkedin: { likes: 892, comments: 67 },
      },
    },
  ]

  res.json(posted)
})

// CREATE new post (creates approval files)
router.post('/post', (req, res) => {
  const { content, platforms, scheduleTime } = req.body
  const timestamp = Date.now()
  const id = `post-${timestamp}`

  platforms.forEach(platform => {
    const filePath = getVaultPath('Pending_Approval', `${id}-${platform}.md`)
    const frontmatter = {
      type: 'post',
      platform,
      scheduled: !!scheduleTime,
      scheduleTime: scheduleTime || null,
      createdAt: new Date().toISOString(),
    }

    writeFile(filePath, frontmatter, content)
  })

  global.broadcast({ type: 'posts_created', platforms, count: platforms.length })
  res.json({ success: true, id, platforms, message: 'Posts created for approval' })
})

// SAVE draft
router.post('/draft', (req, res) => {
  const { content, platforms, title } = req.body
  const timestamp = Date.now()
  const id = `draft-${timestamp}`
  const filePath = getVaultPath('Drafts', `${id}.md`)

  const frontmatter = {
    type: 'post',
    title,
    platforms: platforms.join(','),
    createdAt: new Date().toISOString(),
  }

  writeFile(filePath, frontmatter, content)
  res.json({ success: true, id, message: 'Draft saved' })
})

export default router
