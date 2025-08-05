# BriefCard – Product Requirements Document

## 1. Purpose & Vision  
Enable LINE users to turn any shared link into an instant, visually rich preview **card** with one-tap actions to save, share, or schedule later reading. BriefCard lowers the friction of knowledge capture and sharing inside chat, transforming scattered links into an organized personal knowledge base.

## 2. Problem Statement
* Links pasted into chat are hard to skim and frequently get buried.  
* Users lack a lightweight way to bookmark, organise, and revisit interesting articles without leaving LINE.

## 3. Goals & Success Metrics

| Goal                       | KPI                                           | Target (P0) |
|----------------------------|-----------------------------------------------|-------------|
| Improve link comprehension | Avg. time to decide whether to open a link    | **< 5 s** (P75) |
| Boost article revisit rate | % of saved links revisited within 7 days      | **> 30 %** |
| Drive feature adoption     | MAUs who used at least one BriefCard action   | **> 40 %** of bot MAU |

## 4. Key Features

### 4.1 Smart Link Parsing
* Detect URL in incoming message.  
* Backend crawler fetches **title, hero image, source domain, publish date, author, canonical link**.  
* Run AI summariser (≈ 100-120 tokens) to produce a concise abstract.  
* Fallbacks: default image if no `og:image`; truncated domain if title missing.

### 4.2 LINE Card Rendering
* Compose **Flex Message** bubble containing hero image, title, **main content (first 100 chars)**, and 3 **action buttons** arranged as:
  - **Edit Card** (Primary button, top position)
  - **Read Original** (Secondary, bottom-left) 
  - **Save Bookmark** (Secondary, bottom-right)
* **Image Fallback Strategy**: Use hero image → page preview image → icon.png if unavailable
* Use **Flex Message Simulator** during design for rapid preview.

### 4.3 Quick-Action Buttons
1. **Edit Card** → Opens **LIFF Edit Page** with full bookmark customization options.
2. **Read Original** → Direct link to original webpage (URI action).
3. **Save Bookmark** → Quick-save to default "稍後閱讀" folder with confirmation.

### 4.4 LIFF Interfaces
* **My Library** – sortable grid / list view with folders.  
* **Edit Card Page** – Full bookmark customization interface containing:
  - Link title (editable)
  - Preview image display
  - Folder selector (with "稍後閱讀" as default)
  - Personal notes text area
  - **Generate AI Summary** button (adds summary to notes, *Phase 2 feature*)
  - **Share** and **Save Changes** action buttons
* **Profile** – notification schedule, time-zone, account linking, storage quota.

### 4.5 Daily Reminder Push
* Serverless cron (e.g., Cloud Scheduler) triggers at user-configured time to push up to *n* unread cards as a carousel.

## 5. User Personas & Stories

| Persona            | Story |
|--------------------|-------|
| Busy Professional  | “When I paste an insightful article in chat, I want a short preview so colleagues immediately know what it is.” |
| Content Curator    | “After scanning headlines all day, I want to bulk save good pieces into themed folders without leaving LINE.” |
| Learner on-the-go  | “I forward interesting links into the bot and every night at 21:00 I receive a digest to read.” |

## 6. User Flow (Happy Path)

1. User pastes URL → Bot receives webhook.  
2. Backend fetches metadata + main content (≤ 2 s).  
3. Bot replies with Flex Card showing title, image, and content preview (100 chars).  
4. User taps **Edit Card** → Opens LIFF Edit Page.
5. User customizes folder, adds personal notes, optionally generates AI summary.
6. User saves changes → Bookmark stored in selected folder; user returns to LINE.

## 7. Functional Requirements

| ID   | Requirement |
|------|-------------|
| FR-01 | Detect URLs in text (regex, max 3 per message); ignore non-HTTP schemes. |
| FR-02 | Crawler must return metadata within **1.5 s**; else use fallback template. |
| FR-03 | Summariser model supports Chinese & English; latency budget ≤ 700 ms. |
| FR-04 | Generate Flex Message card with main content (100 chars), hero image, and 3-button layout. |
| FR-05 | Edit Card button opens LIFF page with title, image, folder selector, and notes input. |
| FR-06 | Save Bookmark action stores to default "稍後閱讀" folder with confirmation. |
| FR-07 | LIFF Edit Page supports folder management, personal notes, and bookmark customization. |
| FR-08 | Generate AI Summary feature appends intelligent summary to user notes (*Phase 2*). |
| FR-09 | Share action from LIFF invokes Share Target Picker with pre-filled content. |
| FR-10 | Library LIFF supports folder CRUD, drag-to-reorder, pagination. |
| FR-11 | Support 5 MB total attachment cache per user (configurable). |
| FR-12 | Image fallback hierarchy: hero image → preview image → default icon.png. |

## 8. Non-Functional Requirements
* **Performance**: P95 end-to-end card delivery < 2 s.  
* **Scalability**: Handle 10 QPS burst; auto-scale crawler & summariser.  
* **Security**: OAuth 2.0 / LINE Login; encrypt at rest; comply with PDPA & GDPR.  
* **Privacy**: Do not store full article body; retain only metadata & summary.  
* **Reliability**: 99.5 % monthly availability; graceful degradation if any component fails.

## 9. Technical Architecture
User ⇆ LINE Messaging API ⇆ Bot Webhook (FastAPI) ⇆ Tasks Queue ⇆
├─▶ Crawler (Playwright/Goose)
├─▶ Summariser (OpenAI GPT-4o, 100 tokens)
└─▶ Storage (PostgreSQL + S3 hero cache)
⇵
LIFF Frontend (React + Vite)

*Use Cloud Functions for stateless compute; Cloud Scheduler + Pub/Sub for reminder pushes.*

## 10. Analytics & Logging
* Events: `card_generated`, `action_save`, `action_share`, `reminder_push`, `link_open`.  
* Dashboard: retention, folder growth, average links per user.

## 11. Milestones

| Phase      | Deliverable                                           | Target Date |
|------------|-------------------------------------------------------|-------------|
| **0.5 PoC** | URL detection + static Flex card                     | 15 Sep 2025 |
| **1.0 Beta** | Crawler + AI summary, Save/Read-Later, LIFF Library | 30 Oct 2025 |
| **1.1 GA** | Share picker, reminder scheduler, analytics           | 15 Dec 2025 |

## 12. Open Questions & Risks
1. **Crawler depth** – Full body fetch vs. readability extraction? Impact on latency.  
2. **Hero image licensing** – If original page lacks image, can we auto-pull from Unsplash (license-compatible)?  
3. **Message quota** – Flex messages count toward monthly push limits; need estimation.  
4. **Duplicate links** – How to handle same URL in multiple chats? Suggest dedupe per user vs. global.  
5. **Multi-device sync** – Library sync if user logs in from PC & mobile.

## 13. Appendix – Sample Flex Message JSON (truncated)
```json
{
  "type": "bubble",
  "hero": {
    "type": "image",
    "url": "{heroUrl}",
    "size": "full",
    "aspectRatio": "16:9"
  },
  "body": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      { "type": "text", "text": "{title}", "weight": "bold", "wrap": true },
      { "type": "text", "text": "{mainContent100chars}", "size": "sm", "wrap": true, "margin": "md" },
      { "type": "text", "text": "{source} • {date}", "size": "xs", "color": "#8E8E93", "margin": "sm" },
      {
        "type": "button",
        "style": "primary", 
        "action": { "type": "uri", "uri": "{liffEditUrl}", "label": "✏️ 編輯卡片" },
        "margin": "md"
      }
    ]
  },
  "footer": {
    "type": "box",
    "layout": "horizontal",
    "spacing": "sm",
    "contents": [
      {
        "type": "button",
        "style": "secondary",
        "action": { "type": "uri", "uri": "{originalUrl}", "label": "📖 閱讀原文" }
      },
      {
        "type": "button", 
        "style": "secondary",
        "action": { "type": "postback", "data": "save|{id}", "label": "💾 保存書籤" }
      }
    ]
  }
}


References: LINE Flex Message docs, Flex Simulator, LIFF Share Target Picker, Scheduled API calls.

makefile
Copy
Edit
::contentReference[oaicite:0]{index=0}


Deepseek API Key: "sk-9431c157fec84cf7ab2683f05806bf3b"
openrouter API Key: "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"