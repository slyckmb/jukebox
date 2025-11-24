# Jukebox Master Roadmap - One Simple Plan

**Current Version**: 0.4.0-dev
**Last Updated**: 2025-11-24

---

## ✅ What's Already Done

- ✅ Stage 0: Repository separation
- ✅ Stage 1: Error message cleanup
- ✅ Stage 2: Duplicate detection
- ✅ Album requirement enforced
- ✅ Container running and tested

**You have a working app!**

---

## 🎯 THE BIG PICTURE - What Users Need

```
User Journey:
1. Type artist/album (with typos, wrong case) → ✅ Works easily
2. Submit request → ✅ No duplicates, friendly errors
3. See download progress → ❌ NOT IMPLEMENTED
4. Click "Listen Now" → ❌ NOT IMPLEMENTED
5. Music plays! → ❌ THIS IS THE GOAL!
```

**We're 60% there. Steps 3-5 are the money shot.**

---

## 🚀 THE NEXT 3 FEATURES (In Order)

### PRIORITY 1: Lidarr Status Tracking (THE MONEY SHOT) ⭐⭐⭐⭐⭐

**Time**: 1.5-2 hours
**Why**: This completes the user journey - they see progress and can listen!

**What it does:**
- Shows "Downloading (3 of 10 albums)" with progress bar
- When complete → Shows [🎬 Plex] [🎞️ Jellyfin] [🎵 Navidrome] buttons
- Click button → Music plays!

**This is what makes the app USEFUL!**

---

### PRIORITY 2: Fuzzy Autocomplete (REDUCE ERRORS) ⭐⭐⭐⭐

**Time**: 2-3 hours
**Why**: Users type "beatels" → App finds "The Beatles". Reduces failed requests by 80%+

**What it does:**
- Type "pink f" → Dropdown shows "Pink Floyd"
- Tap to select → Auto-fills correct name
- Works with any case, typos
- Mobile-friendly tap targets

**This prevents 80% of errors!**

---

### PRIORITY 3: Basic UI Cleanup (QUICK WINS) ⭐⭐

**Time**: 2-3 hours total (4 small features)
**Why**: Makes app feel polished and professional

**What it includes:**
1. Show/Hide Failed Toggle (20 min) - Clean up view
2. Delete Request Button (45 min) - Remove old requests
3. Status Filter Pills (40 min) - Filter by status
4. Database Indexes (15 min) - Future-proof performance

**These are all easy and high-impact!**

---

## 📋 Simple Decision Tree

**Question**: What should I work on next?

**Answer**: Choose ONE:

### Option A: Complete the User Journey (RECOMMENDED) ⭐
**Do Priority 1 (Status Tracking) - 1.5-2 hours**
- Result: Users can see progress and listen to music
- This is the "money shot" - the payoff!

### Option B: Prevent Input Errors
**Do Priority 2 (Fuzzy Autocomplete) - 2-3 hours**
- Result: Typing errors reduced by 80%+
- Better mobile experience

### Option C: Quick Polish
**Do Priority 3 (UI Cleanup) - 2-3 hours for all 4**
- Result: App feels more professional
- Easy wins, instant improvements

---

## 🎯 My Recommendation

**Do them in order: Priority 1 → Priority 2 → Priority 3**

**Why?**
1. Priority 1 completes the core value prop (request → listen)
2. Priority 2 makes requesting easier (reduce errors)
3. Priority 3 makes it polished (nice-to-have)

**Total time**: 5-7 hours for all three priorities
**Result**: Production-ready app with complete user journey

---

## 📊 Everything Else (Later)

All the other features we discussed are documented in:
- `docs/ALL-PROPOSED-FEATURES.md` (47 total features)
- `docs/UX-ENHANCEMENTS-FRONTEND.md` (9 UX features)
- `docs/NEXT-STEPS-PLAN.md` (Advanced features)

**Don't worry about those right now!** Focus on Priorities 1-3.

---

## ✋ What NOT to Do Right Now

- ❌ PWA features
- ❌ Push notifications
- ❌ Analytics dashboard
- ❌ Background workers
- ❌ Multi-library support
- ❌ Request scheduling
- ❌ Comprehensive testing
- ❌ Load testing

**These are all future enhancements. Not needed yet!**

---

## 🎬 Next Session - Simple Choice

**Pick ONE:**

### A. Implement Priority 1 (Status Tracking)
**Time**: 1.5-2 hours
**Files**:
- Database migration (1 SQL file)
- Python sync functions (2 functions in app.py)
- HTML/CSS for progress bars and buttons

**Result**: Complete user journey, users can listen to music!

### B. Implement Priority 2 (Fuzzy Autocomplete)
**Time**: 2-3 hours
**Files**:
- JavaScript autocomplete class
- Two backend endpoints
- HTML/CSS for dropdown

**Result**: 80% fewer failed requests, better mobile UX

### C. Implement Priority 3 (UI Cleanup - all 4)
**Time**: 2-3 hours
**Files**:
- JavaScript for filters and toggles
- Simple backend endpoints
- SQL for indexes

**Result**: Polished, professional feel

---

## 💡 If You're Still Confused

**Just answer this**: What's most important to you?

1. **"I want users to see progress and listen to music"** → Do Priority 1
2. **"I want fewer failed requests from typos"** → Do Priority 2
3. **"I want the app to feel polished"** → Do Priority 3

**That's it. Choose one, implement it, done.**

---

## 📁 Document Reference

**This document** (`MASTER-ROADMAP.md`):
- Simple plan, priorities 1-3 only
- Decision tree for what to do next

**Other documents** (for later reference):
- `ALL-PROPOSED-FEATURES.md` - Complete list of 47 features
- `FEATURE-FUZZY-AUTOCOMPLETE.md` - Detailed autocomplete plan
- `STAGE-3-LIDARR-STATUS-SYNC.md` - Detailed status tracking plan
- `UX-ENHANCEMENTS-FRONTEND.md` - 9 frontend improvements

**You only need to read THIS document for next steps!**

---

## ✅ Success Criteria

After Priorities 1-3 are done:

- ✅ Users can request music easily (autocomplete)
- ✅ Users see download progress
- ✅ Users can click "Listen Now" and it works
- ✅ App feels polished (filters, delete, etc.)
- ✅ Minimal failed requests

**Then the app is production-ready and awesome!**

---

## 🎯 Final Answer: What Should I Do Next?

**My recommendation: Implement Priority 1 (Status Tracking)**

**Why?**
- Completes the core user journey
- Users can finally LISTEN to their music
- This is what makes the app useful
- Only 1.5-2 hours
- Clear, focused scope

**After that:** Priority 2 (autocomplete), then Priority 3 (polish)

**Want to start now?** Say "yes" and I'll implement Priority 1!

---

**End of Master Roadmap**

**Remember**: Focus on ONE priority at a time. Don't get overwhelmed by all the other ideas. They're documented for later.
