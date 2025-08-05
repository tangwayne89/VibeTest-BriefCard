#!/usr/bin/env python3
"""
BriefCard - AI 服務工廠
根據配置選擇合適的 AI 服務提供者
"""

import logging
from typing import Dict, Any
from config import settings

logger = logging.getLogger(__name__)

class AIServiceFactory:
    """AI 服務工廠類"""
    
    @staticmethod
    def create_ai_service():
        """
        根據配置建立 AI 服務實例
        
        Returns:
            AI 服務實例，或 None 如果配置無效
        """
        
        provider = settings.ai_service_provider.lower()
        
        if provider == "openrouter":
            if not settings.openrouter_api_key:
                logger.warning("⚠️ OpenRouter API Key 未設定，請檢查 OPENROUTER_API_KEY")
                return None
                
            from ai_service_openrouter import OpenRouterAIService
            logger.info("🤖 使用 OpenRouter AI 服務")
            return OpenRouterAIService()
            
        elif provider == "deepseek":
            if not settings.deepseek_api_key:
                logger.warning("⚠️ DeepSeek API Key 未設定，請檢查 DEEPSEEK_API_KEY")
                return None
                
            from ai_service import AIService
            logger.info("🤖 使用 DeepSeek AI 服務")
            return AIService()
            
        elif provider == "mock":
            # 建立模擬 AI 服務（用於測試）
            logger.info("🤖 使用模擬 AI 服務（測試模式）")
            return MockAIService()
            
        else:
            logger.error(f"❌ 不支援的 AI 服務提供者: {provider}")
            logger.info("📋 支援的提供者: openrouter, deepseek, mock")
            return None
    
    @staticmethod
    def get_available_providers() -> Dict[str, bool]:
        """
        檢查哪些 AI 服務提供者可用
        
        Returns:
            字典包含每個提供者的可用狀態
        """
        
        return {
            "openrouter": bool(settings.openrouter_api_key),
            "deepseek": bool(settings.deepseek_api_key),
            "mock": True  # 模擬服務總是可用
        }

class MockAIService:
    """模擬 AI 服務（用於測試和演示）"""
    
    def __init__(self):
        logger.info("🎭 初始化模擬 AI 服務")
    
    async def generate_summary(self, title: str, content: str, max_length: int = 200) -> str:
        """生成模擬摘要"""
        # 簡單的摘要邏輯：取前幾句話
        sentences = content.replace('\n', ' ').split('.')
        summary = '. '.join(sentences[:2]).strip()
        
        if not summary:
            summary = f"這是關於「{title}」的內容"
        
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
        
        logger.info(f"🎭 模擬摘要生成: {len(summary)} 字")
        return summary
    
    async def extract_keywords(self, title: str, content: str, max_keywords: int = 5) -> list:
        """提取模擬關鍵詞"""
        # 簡單的關鍵詞提取
        words = content.lower().split()
        common_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        
        # 統計詞頻
        word_freq = {}
        for word in words:
            clean_word = ''.join(c for c in word if c.isalnum())
            if len(clean_word) > 2 and clean_word not in common_words:
                word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
        
        # 取前 N 個高頻詞
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:max_keywords]
        result = [word for word, _ in keywords]
        
        # 如果沒有關鍵詞，使用標題中的詞
        if not result and title:
            result = [word for word in title.split() if len(word) > 2][:max_keywords]
        
        logger.info(f"🎭 模擬關鍵詞提取: {result}")
        return result
    
    async def categorize_content(self, title: str, content: str) -> str:
        """模擬內容分類"""
        content_lower = (title + " " + content).lower()
        
        # 簡單的分類邏輯
        if any(kw in content_lower for kw in ['python', 'code', 'programming', 'api', 'github', '程式', '代碼']):
            return "技術/科技"
        elif any(kw in content_lower for kw in ['news', 'breaking', 'report', '新聞', '報導']):
            return "新聞時事"
        elif any(kw in content_lower for kw in ['business', 'money', 'finance', '商業', '財經']):
            return "商業財經"
        elif any(kw in content_lower for kw in ['game', 'movie', 'entertainment', '遊戲', '電影', '娛樂']):
            return "娛樂休閒"
        elif any(kw in content_lower for kw in ['learn', 'education', 'tutorial', '學習', '教育', '教學']):
            return "教育學習"
        else:
            return "其他"
    
    async def analyze_content(self, title: str, content: str) -> Dict[str, Any]:
        """綜合分析內容"""
        logger.info(f"🎭 開始模擬 AI 分析: {title[:50]}...")
        
        # 並行執行分析（實際上是順序執行，但保持接口一致）
        summary = await self.generate_summary(title, content, max_length=50)
        keywords = await self.extract_keywords(title, content)
        category = await self.categorize_content(title, content)
        
        result = {
            "summary": summary,
            "keywords": keywords,
            "category": category
        }
        
        logger.info(f"🎭 模擬 AI 分析完成: 摘要={bool(result['summary'])}, 關鍵詞={len(result['keywords'])}, 分類={result['category']}")
        return result
    
    async def close(self):
        """關閉服務（模擬用，無實際操作）"""
        logger.info("🎭 關閉模擬 AI 服務")

# 建立全域 AI 服務實例
ai_service = AIServiceFactory.create_ai_service()

if __name__ == "__main__":
    print("🏭 AI 服務工廠測試")
    print(f"當前配置: {settings.ai_service_provider}")
    print("可用的服務:")
    
    available = AIServiceFactory.get_available_providers()
    for provider, is_available in available.items():
        status = "✅" if is_available else "❌"
        print(f"  {status} {provider}")
    
    if ai_service:
        print(f"\n✅ 成功建立 AI 服務: {type(ai_service).__name__}")
    else:
        print(f"\n❌ 無法建立 AI 服務")
        print("建議使用模擬服務進行測試：")
        print("export AI_SERVICE_PROVIDER=mock")