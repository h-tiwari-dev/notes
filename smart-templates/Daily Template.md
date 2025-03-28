---
tags: [daily]
alias: <% tp.date.now("YYYY-MM-DD") %>
---

# <% tp.date.now("dddd, MMMM DD, YYYY") %>

[[<% tp.date.now("YYYY-MM-DD", -1) %>|« Yesterday]] | [[<% tp.date.now("YYYY-MM-DD", 1) %>|Tomorrow »]]

## 🗓️ Schedule & Appointments
```dataviewjs
// Optional: Add Dataview query for today's calendar events
// (Requires Calendar plugin and properly formatted events)
```

## 📥 Incoming Tasks
<!-- Tasks migrating from previous days -->
<%* const yesterday = tp.date.now("YYYY-MM-DD", -1) _%>
```dataviewjs
// Optional: Unfinished tasks from previous days
// dv.taskList(dv.pages().file.tasks
//   .where(t => !t.completed && t.text.includes("<%= yesterday %>")))
```

## 🎯 Today's Priorities
- [ ] #task Add priority tasks here

## 💼 Meetings & Notes
### 9:00 AM Standup
- 

### 1:00 PM Project Meeting
- 

## 📝 Daily Notes
### What's important today?
- 

### Journal Entry
- 

## 🔗 Related Links
- 

## 🌟 Daily Highlights
- 

## 📚 Evening Review
### What went well?
- 

### What could be improved?
- 

<%* await tp.file.move("/01. Daily Notes/" + tp.date.now("YYYY-MM-DD")) _%>