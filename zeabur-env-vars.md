# Zeabur 環境變數設定指南

## 🔧 必要環境變數

在 Zeabur 部署時，請設定以下環境變數：

### **Supabase 設定**
```
SUPABASE_URL=https://iimqqijtbylbfkyjodct.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlpbXFxaWp0YnlsYmZreWpvZGN0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQzMTk1NDAsImV4cCI6MjA2OTg5NTU0MH0.ooTwZFFVse8dbsO47DQnQ90hqW0ZydfUzohkhbOYwsE
```

### **LINE Bot 設定**
```
LINE_CHANNEL_ACCESS_TOKEN=5u6VILle7a1JHo6f4JN2llFa5PMi1pdo+hFXpLmHV9LBxt/MlgjI+Pazi2TOucuSwoEuRfUwOWd0A514Zu1Rh34jBmnjYv2Pv4M/9bRAwLP1rVQLNktEsmmNkXhZ48+bsRgRC5gJYOI9wNbj4VbOfQdB04t89/1O/w1cDnyilFU=
LINE_CHANNEL_SECRET=45168b608961f83c37749ca3ba236479
```

### **AI 服務設定**
```
AI_SERVICE_PROVIDER=mock
OPENROUTER_API_KEY=你的OpenRouter_API_Key（可選）
OPENROUTER_MODEL=anthropic/claude-3-haiku:beta（可選）
```

### **應用設定**
```
DEBUG=false
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## 📝 設定步驟

1. **登入 Zeabur**：https://zeabur.com
2. **建立新專案**
3. **連接 GitHub Repository**（建議先推送到 GitHub）
4. **設定環境變數**：在 Variables 頁面逐一添加上述變數
5. **部署**：Zeabur 會自動偵測 Dockerfile 並開始部署

## 🔗 部署後的 Webhook URL

部署成功後，你的 Webhook URL 會是：
```
https://your-app-name.zeabur.app/webhook/line
```

請在 LINE Developers Console 更新這個 URL。

## ✅ 健康檢查

部署後可以訪問：
```
https://your-app-name.zeabur.app/health
```

確認服務是否正常運行。