#!/usr/bin/env python3
"""
BriefCard - LINE Bot 服務
處理 LINE Bot 的所有互動功能
"""

import re
import logging
import json
import asyncio
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, FlexSendMessage, 
    TextSendMessage, PostbackEvent, 
    BubbleContainer
)

from config import settings

# 設定日誌
logger = logging.getLogger(__name__)

class LineBotService:
    """LINE Bot 服務類"""
    
    def __init__(self):
        """初始化 LINE Bot 服務"""
        # 驗證必要配置
        if not settings.line_channel_access_token or not settings.line_channel_secret:
            logger.warning("⚠️ LINE Bot 配置未完整設定")
            self.enabled = False
            return
        
        # 初始化 LINE Bot API
        self.line_bot_api = LineBotApi(settings.line_channel_access_token)
        self.handler = WebhookHandler(settings.line_channel_secret)
        self.enabled = True
        
        # 註冊事件處理器
        self._register_handlers()
        
        logger.info("✅ LINE Bot 服務初始化完成")
    
    def _register_handlers(self):
        """註冊事件處理器"""
        
        @self.handler.add(MessageEvent, message=TextMessage)
        def handle_text_message(event):
            """處理文字訊息"""
            try:
                self._handle_text_message_internal(event)
            except Exception as e:
                logger.error(f"❌ 處理訊息失敗: {e}")
                self._send_error_message(event.reply_token)
        
        @self.handler.add(PostbackEvent)
        def handle_postback(event):
            """處理 PostBack 事件"""
            try:
                self._handle_postback_internal(event)
            except Exception as e:
                logger.error(f"❌ 處理 PostBack 失敗: {e}")
                self._send_error_message(event.reply_token)
    
    def _handle_text_message_internal(self, event: MessageEvent):
        """內部文字訊息處理邏輯"""
        user_message = event.message.text
        user_id = getattr(event.source, 'user_id', 'unknown')
        
        logger.info(f"📨 收到訊息: {user_message} (用戶: {user_id})")
        
        # 檢測 URL
        urls = self._extract_urls(user_message)
        
        if urls:
            # 處理 URL
            self._handle_url_message(event, urls[0], user_id)  # 目前只處理第一個 URL
        else:
            # 處理一般文字訊息
            self._handle_general_message(event, user_message, user_id)
    
    def _handle_postback_internal(self, event: PostbackEvent):
        """內部 PostBack 事件處理邏輯"""
        user_id = getattr(event.source, 'user_id', 'unknown')
        postback_data = event.postback.data
        
        logger.info(f"📨 收到 PostBack: {postback_data} (用戶: {user_id})")
        
        try:
            # 解析 PostBack 數據
            if postback_data.startswith("action=save&bookmark_id="):
                bookmark_id = postback_data.split("bookmark_id=")[1]
                self._handle_save_bookmark(event, bookmark_id, user_id)
            else:
                logger.warning(f"⚠️ 未知的 PostBack 動作: {postback_data}")
                self._reply_message(event.reply_token, "🤔 未知的操作，請重新嘗試。")
        except Exception as e:
            logger.error(f"❌ 處理 PostBack 失敗: {e}")
            self._reply_message(event.reply_token, "😅 處理請求時發生錯誤，請稍後再試。")
    
    def _handle_save_bookmark(self, event: PostbackEvent, bookmark_id: str, user_id: str):
        """處理保存書籤到預設資料夾"""
        logger.info(f"💾 處理保存書籤請求: {bookmark_id} (用戶: {user_id})")
        
        # 創建異步任務來處理書籤保存
        async def save_bookmark_async():
            try:
                from database import db_client
                
                # 獲取用戶的預設資料夾
                default_folder = await db_client.get_default_folder(user_id)
                if not default_folder:
                    logger.error(f"❌ 找不到用戶預設資料夾: {user_id}")
                    self._reply_message(event.reply_token, "😕 無法找到預設資料夾，請稍後再試。")
                    return
                
                # 更新書籤，設置 folder_id
                update_data = {
                    'folder_id': default_folder['id']
                }
                
                result = await db_client.update_bookmark(bookmark_id, update_data)
                if result:
                    folder_name = default_folder.get('name', '稍後閱讀')
                    success_message = f"✅ 書籤已保存到「{folder_name}」資料夾！"
                    self._reply_message(event.reply_token, success_message)
                    logger.info(f"✅ 書籤保存成功: {bookmark_id} → {folder_name}")
                else:
                    self._reply_message(event.reply_token, "😕 保存失敗，請稍後再試。")
                    logger.error(f"❌ 書籤保存失敗: {bookmark_id}")
                    
            except Exception as e:
                logger.error(f"❌ 保存書籤異步處理失敗: {e}")
                self._reply_message(event.reply_token, "😅 保存時發生錯誤，請稍後再試。")
        
        # 在新的事件循環中執行異步操作
        import threading
        def run_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(save_bookmark_async())
            finally:
                loop.close()
        
        # 在背景執行緒中處理異步操作
        thread = threading.Thread(target=run_async)
        thread.daemon = True
        thread.start()
    
    def _extract_urls(self, text: str) -> List[str]:
        """從文字中提取 URL"""
        # URL 正則表達式
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        
        # 驗證 URL 格式
        valid_urls = []
        for url in urls:
            try:
                parsed = urlparse(url)
                if parsed.scheme and parsed.netloc:
                    valid_urls.append(url)
            except Exception:
                continue
        
        return valid_urls
    
    def _handle_url_message(self, event: MessageEvent, url: str, user_id: str):
        """處理包含 URL 的訊息"""
        logger.info(f"🔗 檢測到 URL: {url}")
        
        # 發送確認訊息
        self._reply_message(
            event.reply_token,
            f"📋 正在處理您的連結...\n🔗 {url}\n\n請稍候，我將為您生成預覽卡片！"
        )
        
        # 調用書籤創建 API（模擬內部調用）
        # 註：實際應用中可能需要更完善的內部 API 調用機制
        import asyncio
        asyncio.create_task(self._create_bookmark_from_url(url, user_id, event.reply_token))
    
    async def _create_bookmark_from_url(self, url: str, user_id: str, reply_token: str):
        """創建書籤並發送結果卡片"""
        try:
            # 導入必要模組
            from database import db_client
            from main import process_bookmark_content
            
            # 創建書籤記錄
            bookmark_data = {
                "url": url,
                "user_id": user_id,
                "title": "處理中...",
                "description": "正在分析網頁內容",
                "status": "processing"
            }
            
            bookmark_result = await db_client.create_bookmark(bookmark_data)
            
            if bookmark_result:
                bookmark_id = bookmark_result['id']  # 取得 ID 字符串
                
                # 啟動背景處理
                await process_bookmark_content(bookmark_id, url)
                
                # 等待一段時間後獲取處理結果
                await asyncio.sleep(5)  # 等待處理完成
                
                # 獲取更新後的書籤
                updated_bookmark = await db_client.get_bookmark(bookmark_id)
                
                if updated_bookmark and updated_bookmark.get("status") == "completed":
                    # 發送成功卡片
                    flex_card = self.create_bookmark_flex_card(updated_bookmark)
                    flex_message = FlexSendMessage(
                        alt_text=f"📋 {updated_bookmark.get('title', '新書籤')}",
                        contents=flex_card
                    )
                    
                    # 發送 push message
                    self.line_bot_api.push_message(user_id, flex_message)
                    
                else:
                    # 發送處理失敗訊息
                    self.line_bot_api.push_message(
                        user_id,
                        TextSendMessage(text="😅 抱歉，處理您的連結時遇到問題，請稍後再試。")
                    )
            
        except Exception as e:
            logger.error(f"❌ 創建書籤失敗: {e}")
            self.line_bot_api.push_message(
                user_id,
                TextSendMessage(text="😅 抱歉，處理您的連結時發生錯誤，請稍後再試。")
            )
        
    def _handle_general_message(self, event: MessageEvent, message: str, user_id: str):
        """處理一般文字訊息"""
        
        # 指令處理
        if message.lower() in ['help', '幫助', '/help']:
            self._send_help_message(event.reply_token)
        elif message.lower() in ['library', '書庫', '/library']:
            self._send_library_message(event.reply_token, user_id)
        else:
            # 一般對話
            self._reply_message(
                event.reply_token,
                "👋 您好！我是 BriefCard Bot。\n\n" +
                "📋 請分享任何網頁連結，我會為您生成豐富的預覽卡片！\n\n" +
                "💡 輸入「幫助」查看更多功能"
            )
    
    def _send_help_message(self, reply_token: str):
        """發送幫助訊息"""
        help_text = """
🌟 BriefCard Bot 使用指南

📋 主要功能:
• 分享任何網頁連結，自動生成預覽卡片
• 一鍵保存、分享或稍後閱讀
• AI 智能摘要重點內容

🔧 可用指令:
• 「幫助」- 顯示此說明
• 「書庫」- 查看已保存的書籤
• 直接分享連結 - 生成預覽卡片

💡 小貼士:
只需將網頁連結貼上，我就會自動為您處理！
        """
        self._reply_message(reply_token, help_text.strip())
    
    def _send_library_message(self, reply_token: str, user_id: str):
        """發送書庫訊息"""
        # TODO: 與後端 API 整合，獲取用戶書籤
        library_text = f"""
📚 您的書庫

🔗 正在載入您的書籤...

💡 提示: 這裡將顯示您保存的所有書籤
您可以透過分享連結來添加新的書籤！
        """
        self._reply_message(reply_token, library_text.strip())
    
    def _send_error_message(self, reply_token: str):
        """發送錯誤訊息"""
        self._reply_message(
            reply_token,
            "😅 抱歉，處理您的訊息時發生了錯誤。\n請稍後再試，或聯繫技術支援。"
        )
    
    def _reply_message(self, reply_token: str, text: str):
        """回覆文字訊息"""
        if not self.enabled:
            logger.warning("⚠️ LINE Bot 未啟用，無法發送訊息")
            return
        
        try:
            self.line_bot_api.reply_message(
                reply_token,
                TextSendMessage(text=text)
            )
            logger.info(f"✅ 訊息發送成功: {text[:50]}...")
        except Exception as e:
            logger.error(f"❌ 發送訊息失敗: {e}")
    
    def create_bookmark_flex_card(self, bookmark_data: Dict[str, Any]) -> BubbleContainer:
        """創建書籤 Flex 卡片 - Phase 1 新設計"""
        # 基本資訊
        title = bookmark_data.get('title', '無標題')
        url = bookmark_data.get('url', '')
        bookmark_id = bookmark_data.get('id', '')
        
        # 主要內文：使用 content_markdown 前 100 字（Phase 1 規格）
        main_content = bookmark_data.get('content_markdown', bookmark_data.get('description', ''))
        if main_content and len(main_content) > 100:
            main_content = main_content[:97] + "..."
        elif not main_content:
            main_content = "📋 已保存此網頁書籤"
        
        # 圖片 fallback 策略：首圖 → 預覽圖 → icon.png
        image_url = (bookmark_data.get('image_url') or 
                    bookmark_data.get('preview_image') or 
                    'https://via.placeholder.com/640x360/E3F2FD/1976D2?text=📋')
        
        # 截斷過長的標題
        if len(title) > 60:
            title = title[:57] + "..."
        
        # 構建 Phase 1 Flex 卡片 JSON
        flex_json = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": str(image_url).strip(),
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
                        "text": title,
                        "weight": "bold",
                        "size": "lg",
                        "wrap": True,
                        "maxLines": 2
                    },
                    {
                        "type": "text",
                        "text": main_content,
                        "size": "sm",
                        "color": "#666666",
                        "wrap": True,
                        "maxLines": 4,
                        "margin": "md"
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "uri",
                            "uri": f"https://your-liff-app.com/edit/{bookmark_id}",
                            "label": "編輯卡片"
                        },
                        "margin": "lg"
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
                            "uri": url,
                            "label": "閱讀原文"
                        },
                        "flex": 1
                    },
                    {
                        "type": "button",
                        "style": "secondary",
                        "action": {
                            "type": "postback",
                            "data": f"action=save&bookmark_id={bookmark_id}",
                            "label": "保存書籤"
                        },
                        "flex": 1
                    }
                ]
            }
        }
        
        return BubbleContainer.new_from_json_dict(flex_json)
    
    def send_bookmark_card(self, user_id: str, bookmark_data: Dict[str, Any]):
        """發送書籤卡片給用戶"""
        if not self.enabled:
            logger.warning("⚠️ LINE Bot 未啟用，無法發送卡片")
            return
        
        try:
            flex_card = self.create_bookmark_flex_card(bookmark_data)
            flex_message = FlexSendMessage(
                alt_text=f"📋 {bookmark_data.get('title', '新書籤')}",
                contents=flex_card
            )
            
            # 發送訊息給用戶
            # 注意: 這裡需要 push message，但需要用戶先與 Bot 互動
            logger.info(f"📤 準備發送書籤卡片給用戶: {user_id}")
            
        except Exception as e:
            logger.error(f"❌ 發送書籤卡片失敗: {e}")

# 建立全域實例
line_bot_service = LineBotService()