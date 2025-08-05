# BriefCard 部署指南

## 📋 項目結構
```
cursor_BriefCard/
├── 後端 (FastAPI + Supabase)
│   ├── main.py              # 主要 API 服務
│   ├── line_bot_service.py  # LINE Bot 邏輯
│   ├── database.py          # Supabase 資料庫操作
│   └── ...
└── frontend/               # 前端 (React + Vite)
    ├── src/
    │   ├── EditCard.jsx    # 編輯頁面組件
    │   ├── liff.js         # 網頁版配置（原 LIFF）
    │   └── ...
    └── package.json
```

## 🚀 部署步驟

### 1. 後端部署 (Zeabur)
- ✅ 已完成：目前後端已部署在 Zeabur
- 新增 API 端點：
  - `PATCH /api/bookmarks/{id}` - 更新書籤
  - `GET /api/folders?user_id=xxx` - 獲取資料夾
  - `POST /api/folders` - 建立資料夾

### 2. 前端部署 (Vercel 推薦)

#### 準備工作：
```bash
cd frontend
npm run build
```

#### Vercel 部署：
```bash
npm install -g vercel
vercel --prod
```

#### 設置環境變數：
在 Vercel Dashboard 中設置：
```
VITE_API_BASE_URL=https://your-app.zeabur.app
```

### 3. 更新 LINE Bot 配置

在 `line_bot_service.py` 中更新編輯按鈕 URL：
```python
"uri": f"https://your-frontend-app.vercel.app?bookmarkId={bookmark_id}&userId={user_id or 'anonymous'}"
```

## 🔧 本地開發

### 後端：
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 前端：
```bash
cd frontend
npm run dev
```

## 📱 使用流程

1. 用戶發送網址給 LINE Bot
2. Bot 回覆 Flex Message 卡片
3. 用戶點擊「編輯卡片」按鈕
4. 開啟網頁版編輯頁面
5. 用戶編輯標題、選擇資料夾、添加筆記
6. 點擊「儲存變更」完成

## 🌟 優勢

- ✅ 不受 LINE LIFF 政策限制
- ✅ 更靈活的開發和維護
- ✅ 支援更豐富的 UI 功能
- ✅ 可以在任何瀏覽器中使用
- ✅ 更快速的開發週期