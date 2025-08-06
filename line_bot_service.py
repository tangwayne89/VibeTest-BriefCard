#!/usr/bin/env python3
"""
BriefCard - LINE Bot 智能服務
處理訊息解析、卡片生成和用戶互動
"""

import re
import logging
import asyncio
import threading
from typing import List, Dict, Any
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
    BubbleContainer, RichMenu, RichMenuSize, RichMenuArea, 
    RichMenuBounds, PostbackAction, URIAction
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
        
        # 設置 Rich Menu
        self._setup_rich_menu()
        
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
            elif postback_data == "bookmark_overview":
                self._handle_bookmark_overview(event, user_id)
            elif postback_data == "folders":
                self._handle_folders(event, user_id)
            elif postback_data == "my_profile":
                self._handle_my_profile(event, user_id)
            else:
                logger.warning(f"⚠️ 未知的 PostBack 動作: {postback_data}")
                self._reply_message(event.reply_token, "🤔 未知的操作，請重新嘗試。")
        except Exception as e:
            logger.error(f"❌ 處理 PostBack 失敗: {e}")
            self._reply_message(event.reply_token, "😅 處理請求時發生錯誤，請稍後再試。")
    
    def _handle_save_bookmark(self, event: PostbackEvent, bookmark_id: str, user_id: str):
        """處理保存書籤到預設資料夾 - 改善版"""
        logger.info(f"💾 處理保存書籤請求: {bookmark_id} (用戶: {user_id})")
        
        # 立即發送回饋訊息 (解決問題 3-1: 即時回饋)
        self._reply_message(event.reply_token, "�� 正在保存書籤，請稍候...")
        
        # 創建異步任務來處理書籤保存
        async def save_bookmark_async():
            try:
                from database import db_client
                import uuid
                from datetime import datetime
                
                # 獲取用戶的預設資料夾
                logger.info(f"🔍 查詢用戶預設資料夾: {user_id}")
                default_folder = await db_client.get_default_folder(user_id)
                logger.info(f"🔍 查詢結果: {default_folder}")
                
                if not default_folder:
                    logger.info(f"🔧 自動為用戶創建預設資料夾: {user_id}")
                    # 自動創建預設資料夾 (解決問題 3-2: 找不到預設資料夾)
                    folder_data = {
                        "id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "name": "稍後閱讀",
                        "color": "#1976D2",
                        "is_default": True,
                        "sort_order": 0,
                        "created_at": datetime.utcnow().isoformat()
                    }
                    default_folder = await db_client.create_folder(folder_data)
                    if not default_folder:
                        # 發送失敗訊息
                        self.line_bot_api.push_message(
                            user_id,
                            TextSendMessage(text="😕 無法創建預設資料夾，請稍後再試。")
                        )
                        return
                
                # 更新書籤，設置 folder_id
                update_data = {'folder_id': default_folder['id']}
                
                logger.info(f"🔄 更新書籤資料: {bookmark_id} -> {default_folder['id']}")
                result = await db_client.update_bookmark(bookmark_id, update_data)
                
                if result:
                    folder_name = default_folder.get('name', '稍後閱讀')
                    logger.info(f"✅ 書籤保存成功: {bookmark_id} → {folder_name}")
                    
                    # 發送成功訊息
                    success_message = f"✅ 書籤已保存到「{folder_name}」資料夾！"
                    self.line_bot_api.push_message(
                        user_id,
                        TextSendMessage(text=success_message)
                    )
                else:
                    logger.error(f"❌ 書籤保存失敗: {bookmark_id}")
                    self.line_bot_api.push_message(
                        user_id,
                        TextSendMessage(text="😕 保存失敗，請稍後再試。")
                    )
                    
            except Exception as e:
                logger.error(f"❌ 保存書籤異步處理失敗: {e}")
                self.line_bot_api.push_message(
                    user_id,
                    TextSendMessage(text="😅 保存時發生錯誤，請稍後再試。")
                )
        
        # 在新的事件循環中執行異步操作
        def run_async():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(save_bookmark_async())
            except Exception as e:
                logger.error(f"❌ Threading 異常: {e}")
            finally:
                loop.close()
        
        # 在背景執行緒中處理異步操作
        thread = threading.Thread(target=run_async)
        thread.daemon = True
        thread.start()
    
    def _handle_my_bookmarks(self, event, user_id: str):
        """處理我的書籤請求"""
        logger.info(f"📚 處理我的書籤請求 (用戶: {user_id})")
        
        # 構建書籤歷史頁面 URL
        history_url = f"https://vibe-test-brief-card.vercel.app/bookmark-history.html?userId={user_id}"
        
        # 回覆訊息
        message = f"📚 點擊下方連結查看您的書籤歷史：\n{history_url}\n\n您可以在這裡瀏覽、搜尋和管理所有保存的書籤！"
        self._reply_message(event.reply_token, message)
    
    def _handle_help(self, event):
        """處理幫助請求"""
        help_message = """
🤖 **BriefCard 使用指南**

📋 **基本功能**：
• 發送任何網址給我，我會生成精美的預覽卡片
• 點擊「編輯卡片」可以自定義標題、選擇資料夾、添加筆記
• 點擊「保存書籤」將網址快速保存到預設資料夾

📚 **管理書籤**：
• 使用底部選單的「我的書籤」查看所有保存的連結
• 在編輯頁面可以創建新的資料夾來整理書籤
• 支援搜尋功能，快速找到想要的書籤

✨ **小技巧**：
• 可以在筆記欄添加個人想法和摘要
• 資料夾名稱建議使用主題分類（如：工作、學習、娛樂）
• 定期整理書籤，保持資料夾結構清晰

需要更多幫助嗎？隨時發送訊息給我！ 😊
        """.strip()
        
        self._reply_message(event.reply_token, help_message)
    
    def _handle_analytics(self, event):
        """處理分析請求"""
        analytics_message = """
📊 **使用分析功能即將推出！**

🚀 **即將提供的分析功能**：
• 📈 書籤保存趨勢圖表
• 🏷️ 最常保存的網域統計  
• ⏰ 使用時間分佈分析
• 📚 資料夾使用情況
• 🔥 熱門書籤排行榜

📅 **預計上線時間**：Phase 5 開發階段

敬請期待更多精彩功能！ ✨
        """.strip()
        
        self._reply_message(event.reply_token, analytics_message)
    
    def _handle_bookmark_overview(self, event, user_id: str):
        """處理書籤總覽請求"""
        logger.info(f"📊 處理書籤總覽請求 (用戶: {user_id})")
        
        # 構建書籤歷史頁面 URL
        overview_url = f"https://vibe-test-brief-card.vercel.app/bookmark-history.html?userId={user_id}"
        
        # 回覆訊息
        message = f"📊 **書籤總覽**\n\n點擊下方連結查看您的書籤總覽：\n{overview_url}\n\n✨ **功能特色**：\n• 📖 瀏覽所有保存的書籤\n• 🔍 快速搜尋功能\n• 📊 使用統計資訊\n• 📅 按時間排序檢視"
        self._reply_message(event.reply_token, message)
    
    def _handle_folders(self, event, user_id: str):
        """處理資料夾請求"""
        logger.info(f"📁 處理資料夾請求 (用戶: {user_id})")
        
        message = f"""📁 **資料夾管理**

🚀 **即將推出的資料夾功能**：
• 📂 建立和管理自訂資料夾
• 🎨 設定資料夾顏色和圖示
• 📊 查看每個資料夾的書籤統計
• 🔄 拖拉排序資料夾順序
• 📋 批量移動書籤到資料夾

📅 **預計上線時間**：Phase 2 開發階段

目前您可以在編輯卡片時創建和選擇資料夾！ ✨"""
        
        self._reply_message(event.reply_token, message)
    
    def _handle_my_profile(self, event, user_id: str):
        """處理我的個人設定請求"""
        logger.info(f"👤 處理個人設定請求 (用戶: {user_id})")
        
        message = f"""👤 **個人設定**

🚀 **即將推出的個人功能**：
• ⏰ 每日提醒時間設定
• 🌍 時區和語言偏好
• 🔗 帳戶連結和同步
• 💾 儲存配額管理
• 📈 個人使用分析
• 🔔 通知偏好設定

📅 **預計上線時間**：Phase 3 開發階段

感謝您使用 BriefCard！ 😊"""
        
        self._reply_message(event.reply_token, message)
    
    def _setup_rich_menu(self):
        """設置 Rich Menu 底部選單"""
        try:
            # 創建 Rich Menu
            rich_menu = RichMenu(
                size=RichMenuSize(width=2500, height=1686),
                selected=False,
                name="BriefCard 主選單",
                chat_bar_text="選單",
                areas=[
                    RichMenuArea(
                        bounds=RichMenuBounds(x=0, y=0, width=833, height=1686),
                        action=PostbackAction(data="bookmark_overview", label="書籤總覽")
                    ),
                    RichMenuArea(
                        bounds=RichMenuBounds(x=833, y=0, width=834, height=1686),
                        action=PostbackAction(data="folders", label="資料夾")
                    ),
                    RichMenuArea(
                        bounds=RichMenuBounds(x=1667, y=0, width=833, height=1686),
                        action=PostbackAction(data="my_profile", label="我的")
                    )
                ]
            )
            
            # 創建 Rich Menu
            rich_menu_id = self.line_bot_api.create_rich_menu(rich_menu)
            logger.info(f"✅ Rich Menu 創建成功: {rich_menu_id}")
            
            # 上傳 Rich Menu 圖片（使用簡單的純色圖片）
            self._upload_rich_menu_image(rich_menu_id)
            
            # 設置為預設 Rich Menu（所有用戶都會看到）
            self.line_bot_api.set_default_rich_menu(rich_menu_id)
            logger.info("✅ Rich Menu 設置為預設選單")
            
            # 儲存 Rich Menu ID 以便後續使用
            self.rich_menu_id = rich_menu_id
            
        except Exception as e:
            logger.error(f"❌ 設置 Rich Menu 失敗: {e}")
            # Rich Menu 失敗不影響主要功能
    
    def _upload_rich_menu_image(self, rich_menu_id: str):
        """上傳 Rich Menu 圖片"""
        try:
            # 創建簡單的 Rich Menu 圖片（2500x1686 像素）
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            # 創建圖片
            img = Image.new('RGB', (2500, 1686), color='#f0f0f0')
            draw = ImageDraw.Draw(img)
            
            # 分割線
            draw.line([(833, 0), (833, 1686)], fill='#cccccc', width=2)
            draw.line([(1667, 0), (1667, 1686)], fill='#cccccc', width=2)
            
            # 添加文字（使用默認字體）
            try:
                # 嘗試使用系統字體
                font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 60)
            except:
                # 如果找不到字體，使用默認字體
                font = ImageFont.load_default()
            
            # 繪製按鈕文字
            draw.text((416, 800), "書籤總覽", fill='#333333', font=font, anchor='mm')
            draw.text((1250, 800), "資料夾", fill='#333333', font=font, anchor='mm')
            draw.text((2083, 800), "我的", fill='#333333', font=font, anchor='mm')
            
            # 轉換為字節流
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=90)
            img_byte_arr.seek(0)
            
            # 上傳圖片
            self.line_bot_api.set_rich_menu_image(rich_menu_id, "image/jpeg", img_byte_arr)
            logger.info("✅ Rich Menu 圖片上傳成功")
            
        except Exception as e:
            logger.error(f"❌ 上傳 Rich Menu 圖片失敗: {e}")
            # 圖片上傳失敗，使用純色背景
    
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
                    flex_card = self.create_bookmark_flex_card(updated_bookmark, user_id)
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
        # 簡化處理，專注核心功能
        if message.lower() in ['help', '幫助', '/help']:
            self._send_help_message(event.reply_token)
        else:
            self._reply_message(
                event.reply_token,
                "👋 歡迎使用 BriefCard！\n\n📋 請分享網頁連結，我會生成精美的預覽卡片\n💡 輸入「幫助」查看功能說明"
            )
    
    def _send_help_message(self, reply_token: str):
        """發送幫助訊息"""
        help_text = """🌟 BriefCard Bot 功能說明

📋 主要功能：
• 分享網頁連結，自動生成預覽卡片
• AI 智能摘要重點內容
• 一鍵保存到個人書庫

💡 使用方法：
直接貼上任何網頁連結即可！"""
        
        self._reply_message(reply_token, help_text)
    

    
    def _send_error_message(self, reply_token: str):
        """發送錯誤訊息"""
        self._reply_message(reply_token, "😅 處理時發生錯誤，請稍後再試！")
    
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
    
    def create_bookmark_flex_card(self, bookmark_data: Dict[str, Any], user_id: str = None) -> BubbleContainer:
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
                            "uri": f"https://vibe-test-brief-card.vercel.app?bookmarkId={bookmark_id}&userId={user_id or 'anonymous'}",
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
            flex_card = self.create_bookmark_flex_card(bookmark_data, user_id)
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