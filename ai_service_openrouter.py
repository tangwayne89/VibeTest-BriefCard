#!/usr/bin/env python3
"""
BriefCard - OpenRouter AI 摘要服務
使用 OpenRouter API 進行內容摘要和分析（免費額度友好）
"""

import httpx
import logging
from typing import Optional, Dict, Any, List
import json

from config import settings

logger = logging.getLogger(__name__)

class OpenRouterAIService:
    """OpenRouter AI 摘要服務類"""
    
    def __init__(self):
        """初始化 OpenRouter AI 服務"""
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        
        # 使用配置中的模型
        self.model = settings.openrouter_model
        # 其他可選免費模型：
        # "microsoft/phi-3-mini-128k-instruct:free"  # 微軟免費模型
        # "google/gemma-2-9b-it:free"  # Google 免費模型
        
        # HTTP 客戶端配置
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://briefcard-poc.vercel.app",  # 你的應用網址
                "X-Title": "BriefCard PoC"  # 應用名稱
            }
        )
    
    async def generate_summary(self, title: str, content: str, max_length: int = 200) -> Optional[str]:
        """
        生成內容摘要
        """
        
        try:
            # 構建提示詞
            prompt = f"""請為以下網頁內容生成一個簡潔的中文摘要，要求：

1. 摘要長度控制在 {max_length} 字以內
2. 突出重點資訊和關鍵內容
3. 語言簡潔易懂
4. 如果是新聞文章，請提到時間、地點、人物等關鍵要素
5. 如果是產品介紹，請提到主要功能和特色

標題：{title}

內容：
{content[:2000]}  # 限制輸入長度

請直接生成摘要（不要額外說明）："""

            # 調用 OpenRouter API
            response = await self._call_openrouter_api(prompt, max_tokens=300)
            
            if response:
                summary = response.strip()
                # 確保摘要不超過指定長度
                if len(summary) > max_length:
                    summary = summary[:max_length-3] + "..."
                
                logger.info(f"✅ OpenRouter 摘要生成成功，長度: {len(summary)} 字")
                return summary
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 生成摘要失敗: {e}")
            return None
    
    async def extract_keywords(self, title: str, content: str, max_keywords: int = 5) -> List[str]:
        """
        提取關鍵詞
        """
        
        try:
            prompt = f"""請從以下網頁內容中提取 {max_keywords} 個最重要的中文關鍵詞，要求：

1. 關鍵詞要能代表內容的核心主題
2. 優先選擇具體的名詞、專業術語或重要概念
3. 每個關鍵詞 2-4 個字
4. 直接返回關鍵詞，用逗號分隔，不要其他說明

標題：{title}

內容：
{content[:1500]}

關鍵詞："""

            response = await self._call_openrouter_api(prompt, max_tokens=100)
            
            if response:
                # 解析關鍵詞
                keywords = [kw.strip() for kw in response.split(',') if kw.strip()]
                keywords = keywords[:max_keywords]  # 限制數量
                
                logger.info(f"✅ 關鍵詞提取成功: {keywords}")
                return keywords
            
            return []
            
        except Exception as e:
            logger.error(f"❌ 提取關鍵詞失敗: {e}")
            return []
    
    async def categorize_content(self, title: str, content: str) -> Optional[str]:
        """
        內容分類
        """
        
        try:
            prompt = f"""請將以下網頁內容分類到最合適的類別中，從以下類別中選擇一個：

技術/科技、新聞時事、商業財經、娛樂休閒、教育學習、健康醫療、生活資訊、社群媒體、購物消費、工具軟體、其他

標題：{title}

內容：
{content[:1000]}

請直接返回分類名稱："""

            response = await self._call_openrouter_api(prompt, max_tokens=50)
            
            if response:
                category = response.strip()
                logger.info(f"✅ 內容分類: {category}")
                return category
            
            return "其他"
            
        except Exception as e:
            logger.error(f"❌ 內容分類失敗: {e}")
            return "其他"
    
    async def _call_openrouter_api(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """
        調用 OpenRouter API
        """
        
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.3,  # 較低的溫度以獲得更一致的結果
                "stream": False
            }
            
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    return content
                else:
                    logger.error(f"❌ API 回應格式異常: {data}")
                    return None
            else:
                logger.error(f"❌ API 請求失敗: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 調用 OpenRouter API 失敗: {e}")
            return None
    
    async def analyze_content(self, title: str, content: str) -> Dict[str, Any]:
        """
        綜合分析內容，包含摘要、關鍵詞和分類
        """
        
        logger.info(f"🤖 開始 OpenRouter AI 內容分析: {title[:50]}...")
        
        # 並行執行多個分析任務
        import asyncio
        
        tasks = [
            self.generate_summary(title, content),
            self.extract_keywords(title, content),
            self.categorize_content(title, content)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        analysis_result = {
            "summary": results[0] if not isinstance(results[0], Exception) else None,
            "keywords": results[1] if not isinstance(results[1], Exception) else [],
            "category": results[2] if not isinstance(results[2], Exception) else "其他"
        }
        
        logger.info(f"✅ OpenRouter AI 分析完成: 摘要={bool(analysis_result['summary'])}, 關鍵詞={len(analysis_result['keywords'])}, 分類={analysis_result['category']}")
        
        return analysis_result
    
    async def close(self):
        """關閉客戶端連線"""
        await self.client.aclose()

# 建立全域 AI 服務實例
openrouter_ai_service = OpenRouterAIService()

# 測試 OpenRouter AI 服務
async def test_openrouter_service():
    """測試 OpenRouter AI 服務功能"""
    test_title = "Python 程式設計入門教學"
    test_content = """
    Python 是一種高階程式語言，以其簡潔易讀的語法而聞名。
    本教學將介紹 Python 的基本概念，包括變數、函數、迴圈等。
    Python 廣泛應用於網頁開發、資料科學、人工智慧等領域。
    """
    
    print("🤖 開始測試 OpenRouter AI 服務...")
    
    # 測試綜合分析
    result = await openrouter_ai_service.analyze_content(test_title, test_content)
    
    print(f"摘要: {result['summary']}")
    print(f"關鍵詞: {result['keywords']}")
    print(f"分類: {result['category']}")
    
    await openrouter_ai_service.close()

if __name__ == "__main__":
    import asyncio
    print("🤖 OpenRouter AI 服務測試")
    asyncio.run(test_openrouter_service())