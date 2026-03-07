import express from 'express'
import { readVaultFiles, getVaultPath, moveFile } from '../vault-reader.js'

const router = express.Router()

// GET all emails needing action
router.get('/', (req, res) => {
  const files = readVaultFiles('Needs_Action')
  const emailFiles = files.filter(f => f.frontmatter.type === 'email')

  if (emailFiles.length === 0) {
    return res.json([
      {
        id: 'email-1',
        from: 'customer@example.com',
        subject: 'Question about pricing',
        preview: 'Hi, I wanted to ask about your enterprise pricing...',
        time: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
        priority: 'high',
        type: 'email',
      },
      {
        id: 'email-2',
        from: 'team@company.com',
        subject: 'Weekly standup notes',
        preview: 'Here are this week\'s standup notes...',
        time: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        priority: 'medium',
        type: 'email',
      },
      {
        id: 'email-3',
        from: 'support@service.io',
        subject: 'Monthly report',
        preview: 'Your monthly service report is ready...',
        time: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        priority: 'low',
        type: 'email',
      },
    ])
  }

  const emails = emailFiles.map(file => ({
    id: file.id,
    ...file.frontmatter,
    preview: file.content.substring(0, 100),
  }))

  res.json(emails)
})

// GET single email
router.get('/:id', (req, res) => {
  const files = readVaultFiles('Needs_Action')
  const email = files.find(f => f.id === req.params.id && f.frontmatter.type === 'email')

  if (!email) {
    return res.status(404).json({ error: 'Email not found' })
  }

  res.json({
    id: email.id,
    ...email.frontmatter,
    body: email.content,
  })
})

// APPROVE and send email
router.post('/:id/send', (req, res) => {
  const { id } = req.params
  const sourcePath = getVaultPath('Needs_Action', `${id}.md`)
  const destPath = getVaultPath('Done', `${id}.md`)

  const success = moveFile(sourcePath, destPath)
  if (success) {
    global.broadcast({ type: 'email_sent', id })
    res.json({ success: true, message: 'Email sent' })
  } else {
    res.status(500).json({ success: false, message: 'Failed to send email' })
  }
})

// REJECT email
router.post('/:id/reject', (req, res) => {
  const { id } = req.params
  const sourcePath = getVaultPath('Needs_Action', `${id}.md`)
  const destPath = getVaultPath('Rejected', `${id}.md`)

  const success = moveFile(sourcePath, destPath)
  if (success) {
    global.broadcast({ type: 'email_rejected', id })
    res.json({ success: true, message: 'Email rejected' })
  } else {
    res.status(500).json({ success: false, message: 'Failed to reject email' })
  }
})

export default router
