#!/usr/bin/env python3
"""
BriefCard - 爬蟲服務
使用 Crawl4AI 進行網頁內容提取
"""

import asyncio
import time
from typing import Optional, Dict, Any
import logging
from urllib.parse import urlparse
import re

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from config import settings

logger = logging.getLogger(__name__)

class WebCrawlerService:
    """網頁爬蟲服務類"""
    
    def __init__(self):
        """初始化爬蟲服務"""
        self.browser_config = BrowserConfig(
            headless=True,
            viewport_width=1920,
            viewport_height=1080,
            # 反爬蟲設定
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # 使用最簡單、最穩定的設定
        self.crawl_config = CrawlerRunConfig(
            # 調整超時設定
            page_timeout=15000,  # 15秒超時
            # 不等待任何特定事件，立即獲取內容
            # wait_for 參數完全移除，使用默認行為
            # 關閉所有可能造成問題的選項
            remove_overlay_elements=False,
            simulate_user=False,
            override_navigator=False,
            delay_before_return_html=3.0,  # 給內容更多時間載入
        )
    
    def is_valid_url(self, url: str) -> bool:
        """驗證 URL 是否有效"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def clean_url(self, url: str) -> str:
        """清理和標準化 URL"""
        # 移除追蹤參數
        url = re.sub(r'[?&](utm_[^&]*|fbclid|gclid|_ga|ref)[^&]*', '', url)
        url = re.sub(r'[?&]$', '', url)  # 移除末尾的 ? 或 &
        
        # 確保有協議
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url
    
    async def extract_content(self, url: str) -> Optional[Dict[str, Any]]:
        """
        提取網頁內容
        
        Args:
            url: 要爬取的網址
            
        Returns:
            Dict 包含提取的內容資訊，或 None 如果失敗
        """
        
        # 驗證和清理 URL
        if not self.is_valid_url(url):
            logger.error(f"❌ 無效的 URL: {url}")
            return None
        
        cleaned_url = self.clean_url(url)
        logger.info(f"🕷️ 開始爬取: {cleaned_url}")
        
        start_time = time.time()
        
        try:
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                result = await crawler.arun(
                    url=cleaned_url,
                    config=self.crawl_config
                )
                
                if not result.success:
                    error_msg = getattr(result, 'error_message', '未知錯誤')
                    logger.error(f"❌ 爬取失敗: {error_msg}")
                    return {"error": error_msg, "url": cleaned_url, "success": False}
                
                # 安全提取基本資訊，處理所有可能的 None 值
                metadata = result.metadata or {}
                title_raw = metadata.get("title") or ""
                desc_raw = metadata.get("description") or ""
                
                content_data = {
                    "url": cleaned_url,
                    "title": (title_raw.strip() if title_raw else "") or self._extract_title_from_content(result.markdown),
                    "description": (desc_raw.strip() if desc_raw else "") or self._extract_description_from_content(result.markdown),
                    "image_url": self._extract_main_image(metadata),
                    "content_markdown": self._truncate_content(result.markdown or ""),
                    "content_text": self._truncate_content(result.cleaned_html or ""),
                    "author": metadata.get("author") or "",
                    "publish_date": metadata.get("published_time") or "",
                    "site_name": metadata.get("site_name") or self._extract_domain(cleaned_url),
                    "success": True,
                    "crawl_duration": round(time.time() - start_time, 2),
                    "word_count": len((result.markdown or "").split()),
                    "status_code": getattr(result, 'status_code', 200)
                }
                
                logger.info(f"✅ 爬取成功: {cleaned_url} ({content_data['crawl_duration']}s)")
                return content_data
                
        except asyncio.TimeoutError:
            logger.error(f"⏰ 爬取逾時: {cleaned_url}")
            return {"error": "爬取逾時", "url": cleaned_url, "success": False}
            
        except ConnectionError as e:
            logger.error(f"🌐 網路連線失敗: {cleaned_url} - {str(e)}")
            return {"error": f"網路連線失敗: {str(e)}", "url": cleaned_url, "success": False}
            
        except Exception as e:
            # 處理 Crawl4AI 特定錯誤
            error_str = str(e)
            if "Page.goto: Timeout" in error_str:
                logger.error(f"⏰ 頁面載入超時: {cleaned_url}")
                return {"error": "頁面載入超時", "url": cleaned_url, "success": False}
            elif "net::ERR_" in error_str:
                logger.error(f"🌐 網路錯誤: {cleaned_url}")
                return {"error": "網路錯誤", "url": cleaned_url, "success": False}
            else:
                logger.error(f"❌ 爬取異常: {cleaned_url} - {error_str}")
                return {"error": error_str, "url": cleaned_url, "success": False}
    
    def _extract_title_from_content(self, content: str) -> str:
        """從內容中提取標題"""
        if not content:
            return ""
        
        # 尋找第一個 # 標題
        lines = content.split('\n')
        for line in lines:
            if line.strip().startswith('# '):
                return line.strip()[2:].strip()
        
        # 如果沒有 # 標題，取前 100 字符作為標題
        return content[:100].strip()
    
    def _extract_description_from_content(self, content: str) -> str:
        """從內容中提取描述"""
        if not content:
            return ""
        
        # 移除標題，取前 300 字符作為描述
        lines = content.split('\n')
        text_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
        
        if text_lines:
            description = ' '.join(text_lines)
            return description[:300].strip()
        
        return ""
    
    def _extract_main_image(self, metadata: Dict[str, Any]) -> str:
        """提取主要圖片 URL"""
        # 嘗試不同的圖片欄位
        image_fields = ['og:image', 'twitter:image', 'image', 'thumbnail']
        
        for field in image_fields:
            if field in metadata and metadata[field]:
                return metadata[field]
        
        return ""
    
    def _extract_domain(self, url: str) -> str:
        """從 URL 提取網域名稱"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except:
            return ""
    
    def _truncate_content(self, content: str) -> str:
        """截斷內容到指定長度"""
        if not content:
            return ""
        
        if len(content) <= settings.max_content_length:
            return content
        
        # 在單詞邊界截斷
        truncated = content[:settings.max_content_length]
        last_space = truncated.rfind(' ')
        
        if last_space > 0:
            truncated = truncated[:last_space]
        
        return truncated + "..."

# 建立全域爬蟲服務實例
crawler_service = WebCrawlerService()

# 測試爬蟲功能
async def test_crawler():
    """測試爬蟲功能"""
    test_url = "https://example.com"
    result = await crawler_service.extract_content(test_url)
    
    if result:
        print("✅ 爬蟲測試成功")
        print(f"標題: {result.get('title')}")
        print(f"描述: {result.get('description')}")
        print(f"耗時: {result.get('crawl_duration')}s")
    else:
        print("❌ 爬蟲測試失敗")

if __name__ == "__main__":
    print("🕷️ 爬蟲服務測試")
    asyncio.run(test_crawler())