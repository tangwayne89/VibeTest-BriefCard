# BriefCard PoC 技術實作指南

## 🚀 快速開始指南

### 1. Supabase 設置

#### 1.1 建立 Supabase 專案
```bash
# 1. 前往 https://supabase.com 建立新專案
# 2. 記錄以下資訊：
#    - Project URL
#    - Anon Key
#    - Service Role Key
```

#### 1.2 資料庫結構設計
```sql
-- 使用者表 (利用 Supabase Auth)
-- auth.users 已由 Supabase 提供

-- 資料夾表
CREATE TABLE folders (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  color TEXT DEFAULT '#1976D2',
  is_default BOOLEAN DEFAULT FALSE,
  sort_order INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 連結收藏表  
CREATE TABLE bookmarks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  folder_id UUID REFERENCES folders(id) ON DELETE SET NULL,
  url TEXT NOT NULL,
  title TEXT,
  description TEXT,
  image_url TEXT,
  content_markdown TEXT,
  summary TEXT,
  notes TEXT,
  tags TEXT[],
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 分享表
CREATE TABLE shares (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  bookmark_id UUID REFERENCES bookmarks(id) ON DELETE CASCADE,
  share_token TEXT UNIQUE NOT NULL,
  expires_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 提醒表
CREATE TABLE reminders (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  bookmark_id UUID REFERENCES bookmarks(id) ON DELETE CASCADE,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  remind_at TIMESTAMP WITH TIME ZONE NOT NULL,
  message TEXT,
  is_sent BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 索引優化
CREATE INDEX idx_folders_user_id ON folders(user_id);
CREATE INDEX idx_folders_sort_order ON folders(sort_order);
CREATE INDEX idx_bookmarks_user_id ON bookmarks(user_id);
CREATE INDEX idx_bookmarks_folder_id ON bookmarks(folder_id);
CREATE INDEX idx_bookmarks_created_at ON bookmarks(created_at);
CREATE INDEX idx_shares_token ON shares(share_token);
CREATE INDEX idx_reminders_remind_at ON reminders(remind_at) WHERE NOT is_sent;
```

#### 1.3 Row Level Security (RLS) 設定
```sql
-- 啟用 RLS
ALTER TABLE folders ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE shares ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;

-- 資料夾政策
CREATE POLICY "Users can view own folders" ON folders FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own folders" ON folders FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own folders" ON folders FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own folders" ON folders FOR DELETE USING (auth.uid() = user_id);

-- 書籤政策
CREATE POLICY "Users can view own bookmarks" ON bookmarks FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own bookmarks" ON bookmarks FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own bookmarks" ON bookmarks FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own bookmarks" ON bookmarks FOR DELETE USING (auth.uid() = user_id);

-- 分享政策 (允許公開訪問有效的分享)
CREATE POLICY "Anyone can view valid shares" ON shares FOR SELECT USING (expires_at IS NULL OR expires_at > now());

-- 提醒政策
CREATE POLICY "Users can manage own reminders" ON reminders FOR ALL USING (auth.uid() = user_id);
```

### 2. Crawl4AI 整合

#### 2.1 安裝與設置
```bash
# 安裝 Crawl4AI
pip install crawl4ai

# 初始化瀏覽器
crawl4ai-setup

# 檢查安裝
crawl4ai-doctor
```

#### 2.2 核心爬蟲服務實作
```python
# services/crawler_service.py
import asyncio
import json
from typing import Optional, Dict, Any
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel

class WebPageData(BaseModel):
    title: str
    description: str
    content_markdown: str
    main_image: Optional[str] = None
    favicon: Optional[str] = None
    author: Optional[str] = None
    publish_date: Optional[str] = None
    reading_time: Optional[int] = None  # 分鐘
    language: Optional[str] = None

class CrawlerService:
    def __init__(self, deepseek_api_key: str):
        self.deepseek_api_key = deepseek_api_key
        
    async def extract_page_data(self, url: str) -> Dict[str, Any]:
        """提取網頁完整資訊"""
        
        # 設定 LLM 提取策略
        llm_strategy = LLMExtractionStrategy(
            llm_config=LLMConfig(
                provider="deepseek/deepseek-chat",  # 使用 DeepSeek 降低成本
                api_token=self.deepseek_api_key
            ),
            schema=WebPageData.model_json_schema(),
            extraction_type="schema",
            instruction="""
            請從網頁內容中提取以下資訊：
            - title: 文章標題
            - description: 文章摘要或描述（100-200字）
            - content_markdown: 主要內容轉為 markdown 格式
            - main_image: 主要圖片 URL
            - favicon: 網站圖標 URL
            - author: 作者名稱
            - publish_date: 發布日期
            - reading_time: 預估閱讀時間（分鐘）
            - language: 內容語言（zh, en, ja等）
            
            請確保提取的內容乾淨、結構化，適合後續處理。
            """,
            chunk_token_threshold=8000,
            overlap_rate=0.1,
            apply_chunking=True,
            extra_args={"temperature": 0.1, "max_tokens": 4000}
        )
        
        # 爬蟲配置
        crawl_config = CrawlerRunConfig(
            extraction_strategy=llm_strategy,
            cache_mode=CacheMode.BYPASS,
            # 反爬蟲設定
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            wait_for_images=True,
            remove_overlay_elements=True,
            process_iframes=True
        )
        
        browser_cfg = BrowserConfig(
            headless=True,
            viewport_width=1920,
            viewport_height=1080
        )
        
        try:
            async with AsyncWebCrawler(config=browser_cfg) as crawler:
                result = await crawler.arun(url=url, config=crawl_config)
                
                if result.success:
                    extracted_data = json.loads(result.extracted_content)
                    return {
                        "success": True,
                        "data": extracted_data,
                        "raw_content": result.markdown,
                        "images": result.media.get("images", []),
                        "links": result.links
                    }
                else:
                    return {
                        "success": False,
                        "error": result.error_message
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_summary(self, content: str, max_length: int = 200) -> str:
        """使用 AI 生成內容摘要"""
        # 這裡可以整合 OpenAI 或 DeepSeek API
        # 暫時返回截斷內容
        return content[:max_length] + "..." if len(content) > max_length else content
```

### 3. FastAPI 後端架構

#### 3.1 主要 API 結構
```python
# main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os
from services.crawler_service import CrawlerService
from services.line_service import LineService

app = FastAPI(title="BriefCard API")

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # PoC 階段，生產環境需要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase 客戶端
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

# 服務實例
crawler_service = CrawlerService(os.getenv("DEEPSEEK_API_KEY"))
line_service = LineService(os.getenv("LINE_CHANNEL_SECRET"), os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))

@app.post("/api/bookmarks")
async def create_bookmark(url: str, user_id: str):
    """創建新書籤"""
    try:
        # 爬取網頁資訊
        crawl_result = await crawler_service.extract_page_data(url)
        
        if not crawl_result["success"]:
            raise HTTPException(status_code=400, detail="無法處理此網址")
        
        page_data = crawl_result["data"]
        
        # 儲存到 Supabase
        bookmark_data = {
            "user_id": user_id,
            "url": url,
            "title": page_data["title"],
            "description": page_data["description"],
            "content_markdown": page_data["content_markdown"],
            "image_url": page_data["main_image"]
        }
        
        result = supabase.table("bookmarks").insert(bookmark_data).execute()
        
        return {"success": True, "bookmark": result.data[0]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/line/webhook")
async def line_webhook(request: dict):
    """LINE Bot webhook 處理"""
    return await line_service.handle_webhook(request)
```

### 4. LINE Bot 整合

#### 4.1 LINE 服務實作
```python
# services/line_service.py
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, FlexSendMessage
import re
import json

class LineService:
    def __init__(self, channel_secret: str, channel_access_token: str):
        self.line_bot_api = LineBotApi(channel_access_token)
        self.handler = WebhookHandler(channel_secret)
        
    def is_url(self, text: str) -> bool:
        """檢測是否為 URL"""
        url_pattern = r'https?://[^\s]+'
        return bool(re.search(url_pattern, text))
    
    def create_bookmark_card(self, bookmark_data: dict) -> dict:
        """創建書籤 Flex Message 卡片 - Phase 1 設計"""
        # 內文截斷策略：使用主要內文前 100 字
        main_content = bookmark_data.get('content_markdown', bookmark_data.get('description', ''))
        content_preview = main_content[:100] + "..." if len(main_content) > 100 else main_content
        
        # 圖片 fallback 策略：首圖 → 預覽圖 → icon.png
        image_url = (bookmark_data.get('image_url') or 
                    bookmark_data.get('preview_image') or 
                    'https://your-domain.com/icon.png')
        
        return {
            "type": "flex", 
            "altText": f"📋 {bookmark_data['title']}",
            "contents": {
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": image_url,
                    "size": "full",
                    "aspectRatio": "16:9",
                    "aspectMode": "cover"
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": bookmark_data['title'],
                            "weight": "bold",
                            "size": "lg",
                            "wrap": True
                        },
                        {
                            "type": "text",
                            "text": content_preview,
                            "size": "sm",
                            "color": "#666666",
                            "wrap": True,
                            "margin": "md"
                        },
                        {
                            "type": "button",
                            "style": "primary",
                            "action": {
                                "type": "uri",
                                "uri": f"https://your-liff-app.com/edit/{bookmark_data['id']}",
                                "label": "✏️ 編輯卡片"
                            },
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
                            "action": {
                                "type": "uri",
                                "uri": bookmark_data['url'],
                                "label": "📖 閱讀原文"
                            }
                        },
                        {
                            "type": "button",
                            "style": "secondary", 
                            "action": {
                                "type": "postback",
                                "data": f"save|{bookmark_data['id']}",
                                "label": "💾 保存書籤"
                            }
                        }
                    ]
                }
            }
        }
```

### 5. 部署設定

#### 5.1 環境變數設定
```bash
# .env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

LINE_CHANNEL_SECRET=your_line_channel_secret
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token

DEEPSEEK_API_KEY=your_deepseek_api_key
OPENAI_API_KEY=your_openai_api_key (備用)

# Vercel 部署時使用
ENVIRONMENT=production
```

#### 5.2 Vercel 部署配置
```json
// vercel.json
{
  "version": 2,
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "main.py"
    }
  ],
  "env": {
    "SUPABASE_URL": "@supabase-url",
    "SUPABASE_ANON_KEY": "@supabase-anon-key"
  }
}
```

### 6. 開發流程建議

#### 6.1 PoC 開發順序
1. **Day 1-2**: 設定 Supabase 專案和資料庫結構
2. **Day 3-4**: 實作基本的 Crawl4AI 爬蟲功能
3. **Day 5-6**: 整合 FastAPI 後端 API
4. **Day 7-8**: 實作 LINE Bot 基本功能
5. **Day 9-10**: 測試和優化

#### 6.2 測試策略
```python
# 測試用例
test_urls = [
    "https://example.com/article",
    "https://medium.com/@test/article", 
    "https://github.com/repo/readme",
    "https://news.ycombinator.com/item?id=123"
]

# 效能測試
import time
async def performance_test():
    start_time = time.time()
    result = await crawler_service.extract_page_data(test_url)
    end_time = time.time()
    print(f"處理時間: {end_time - start_time:.2f} 秒")
```

## 💡 成本優化建議

1. **DeepSeek API**: 比 OpenAI 便宜約 90%，PoC 階段建議使用
2. **Supabase 免費層**: 可支持初期開發和測試
3. **Vercel 免費層**: 適合 PoC 部署
4. **快取策略**: 對相同 URL 在 24 小時內不重複爬取

## 🚨 注意事項

1. **反爬蟲**: 某些網站可能需要特殊處理
2. **速率限制**: 建議加入請求間隔避免被封
3. **錯誤處理**: 確保爬蟲失敗時有適當的回饋
4. **資料清理**: AI 提取的資料需要驗證和清理

準備好開始實作了嗎？我建議從 Supabase 設定開始！