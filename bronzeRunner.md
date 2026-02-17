
<!-- STEP 1: Watcher Chalu Karo -->


# Terminal kholo aur ye command run karo
cd ~/ai_employee_project
./start_watcher.sh


<!-- 
Kya Hoga:

Watcher chalu ho jayega
Drop folder monitor karega
Screen pe dikhe ga: "Monitoring Drop folder..." -->

<!-- STEP 2: File Drop Karo -->

# Naya terminal kholo
cd ~/Documents/AI_Employee_Vault/Drop

# Test file banao
echo "URGENT: Review budget for Q1 project" > test_task.txt
<!-- 
Kya Hoga (10 seconds me):

Watcher ne file detect ki ✅
File copy hui → /Needs_Action folder me
Log me entry ban gayi
Watcher terminal me message aaya: "✅ Created: FILE_test_task_..." -->

<!-- STEP 3: Claude Se Process Karo -->

# Vault me jao
cd ~/Documents/AI_Employee_Vault

# Claude Code se process karo
claude "Use the skill at Skills/process_inbox/SKILL.md to process all items in Needs_Action folder"
```

**Kya Hoga:**
- Claude ne file read ki 📖
- Analysis kiya
- Action plan banaya `/Plans` folder me
- Dashboard update kiya
- Log me entry daali

---

## **📋 Kya Kaam Karta Hai (Simple Flow)**
```
1. Aap File Drop Karo (Drop folder me)
        ↓
2. Watcher Detect Kare (10 seconds me)
        ↓
3. File Uthaye → Needs_Action me dale
        ↓
4. Claude Code Process Kare (aap command do)
        ↓
5. Plan Banaye → Plans folder me
        ↓
6. Dashboard Update Kare
        ↓
7. Done!


 Real Example (Step by Step)
Scenario: Budget review karna hai
1. Watcher Start Karo
bashcd ~/ai_employee_project
./start_watcher.sh

# Screen pe dikhe ga:
# 🚀 Starting Filesystem Watcher
# 📁 Monitoring: /Users/you/Documents/AI_Employee_Vault
# ⏹️  Press Ctrl+C to stop
2. File Drop Karo
bash# Dusre terminal me
echo "Review Q1 budget - deadline Friday" > ~/Documents/AI_Employee_Vault/Drop/budget.txt
```

**3. Watcher Output Dekho**
```
# Pehle terminal me dikhe ga (10 seconds me):
📥 Found 1 new item(s)
📄 Processed: budget.txt → FILE_budget_20260107_103045.md
✅ Created: FILE_budget_20260107_103045.md
4. Check Karo File Ban Gayi
bashls ~/Documents/AI_Employee_Vault/Needs_Action/
# Output: FILE_budget_20260107_103045.md
5. Claude Se Process Karo
bashcd ~/Documents/AI_Employee_Vault

claude "Use the process_inbox skill to analyze all files in Needs_Action"
6. Results Dekho
bash# Plans folder me plan ban gaya
cat Plans/PLAN_budget_*.md

# Dashboard update ho gaya
cat Dashboard.md

# Logs me entry aayi
cat ~/ai_employee_project/logs/ai_employee.log
```

---

## **📊 Folder Structure (Kahan Kya Hai)**
```
AI_Employee_Vault/
│
├── Drop/                    👈 YAHAN FILE DROP KARO
│   └── (aap ka test file)
│
├── Needs_Action/           👈 WATCHER YAHAN FILE DALE GA
│   └── FILE_budget_*.md
│
├── Plans/                  👈 CLAUDE YAHAN PLAN BANAYE GA
│   └── PLAN_budget_*.md
│
├── Done/                   👈 COMPLETE TASKS YAHAN
│
├── Dashboard.md            👈 STATUS CHECK KARO YAHAN
│
└── Skills/                 👈 AI KE INSTRUCTIONS YAHAN
    ├── process_inbox/
    ├── update_dashboard/
    └── ...

🔄 Daily Workflow (Roz Kya Karna Hai)
Morning (Subah)
bash# 1. Watcher start karo
cd ~/ai_employee_project
./start_watcher.sh

# 2. Dashboard check karo
cd ~/Documents/AI_Employee_Vault
cat Dashboard.md

# 3. Agar pending tasks hain, process karo
claude "Use process_inbox skill"
During Day (Din Me)
bash# Jab bhi kaam aaye, file drop karo
echo "Client meeting notes" > ~/Documents/AI_Employee_Vault/Drop/meeting.txt

# Watcher automatically detect karega (10 seconds)
# Needs_Action me file ban jayegi
Evening (Shaam)
bash# Dashboard update karo
cd ~/Documents/AI_Employee_Vault
claude "Use update_dashboard skill to refresh status"

# Summary dekho
cat Dashboard.md

# Kal ke liye ready

💡 Useful Commands (Yaad Rakho)
Check Watcher Running Hai Ya Nahi
bashps aux | grep filesystem_watcher
# Agar running hai to process dikhe ga
Watcher Stop Karo
bash# Watcher terminal me Ctrl+C press karo
Dashboard Dekho
bashcd ~/Documents/AI_Employee_Vault
cat Dashboard.md
# Ya Obsidian me open karo
Pending Tasks Dekho
bashls ~/Documents/AI_Employee_Vault/Needs_Action/
Plans Dekho
bashls ~/Documents/AI_Employee_Vault/Plans/
cat Plans/PLAN_*.md
Logs Dekho (Kya Hua)
bashtail -f ~/ai_employee_project/logs/ai_employee.log

🎬 Complete Example (Shuru Se End Tak)
bash# ==== TERMINAL 1: Watcher ====
cd ~/ai_employee_project
./start_watcher.sh

# Output:
# 🚀 Starting AI Employee - Filesystem Watcher
# 📁 Monitoring Drop folder...


# ==== TERMINAL 2: Testing ====

# Test 1: Simple task
echo "Call client about invoice" > ~/Documents/AI_Employee_Vault/Drop/call_client.txt

# Wait 10 seconds...

# Check file created
ls ~/Documents/AI_Employee_Vault/Needs_Action/
# Output: FILE_call_client_20260107_103045.md

# Process with Claude
cd ~/Documents/AI_Employee_Vault
claude "Use process_inbox skill to handle all tasks in Needs_Action"

# Check results
ls Plans/
# Output: PLAN_call_client_20260107_103046.md

cat Plans/PLAN_call_client_20260107_103046.md
# Shows: Action plan with steps

# Check dashboard
cat Dashboard.md
# Shows: Updated counts

# Done! ✅

🚨 Common Issues & Solutions
❌ Watcher nahi chal raha
bash# Check .env file
cat ~/ai_employee_project/.env
# Verify OBSIDIAN_VAULT_PATH correct hai

# Manually test
cd ~/ai_employee_project/watchers
python3 filesystem_watcher.py
❌ File detect nahi ho rahi
bash# Check Drop folder path
echo $HOME/Documents/AI_Employee_Vault/Drop

# Manually file dale
touch ~/Documents/AI_Employee_Vault/Drop/test.txt

# Wait 10 seconds

# Check logs
tail ~/ai_employee_project/logs/ai_employee.log
❌ Claude Code nahi chal raha
bash# Check Claude Code installed hai
claude --version

# Vault directory me ho
cd ~/Documents/AI_Employee_Vault

# Simple test
claude "list all files"

✅ Success Indicators (Sab Theek Hai)
Ye sab dikhe to system working hai:

✅ Watcher terminal me "Monitoring..." dikhe
✅ File drop karo → 10 sec me Needs_Action me aaye
✅ Claude command run kare → Plans folder me plan bane
✅ Dashboard.md update ho
✅ Logs me entries aaye


🎯 Bottom Line
3 Cheezein Karo Bas:

Start Watcher → ./start_watcher.sh
Drop File → Drop folder me file dalo
Run Claude → claude "Use process_inbox skill"

Baaki sab automatic! 🚀