#!/usr/bin/env python3
"""
智能修復應用器
自動應用所有 BriefCard 修復
"""
import re

def apply_line_bot_fix():
    """應用 LINE Bot 服務修復"""
    print("🔧 正在修復 LINE Bot 服務...")
    
    # 讀取原始文件
    with open('line_bot_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 新的 _handle_save_bookmark 方法
    new_method = '''    def _handle_save_bookmark(self, event: PostbackEvent, bookmark_id: str, user_id: str):
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
        thread.start()'''
    
    # 使用正則表達式替換整個方法
    pattern = r'    def _handle_save_bookmark\(self, event: PostbackEvent, bookmark_id: str, user_id: str\):.*?        thread\.start\(\)'
    
    new_content = re.sub(pattern, new_method, content, flags=re.DOTALL)
    
    # 寫回文件
    with open('line_bot_service.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ LINE Bot 服務修復完成！")

def apply_backend_api_fix():
    """應用後端 API 修復"""
    print("🔧 正在添加後端 API 端點...")
    
    # 讀取原始文件
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 新的 API 端點
    new_endpoint = '''
@app.post("/api/send-updated-card")
async def send_updated_card(request: dict):
    """發送更新後的書籤卡片到 LINE (解決問題 1: 編輯後跳轉)"""
    try:
        bookmark_id = request.get("bookmark_id")
        user_id = request.get("user_id")
        
        if not bookmark_id or not user_id:
            raise HTTPException(status_code=400, detail="缺少必要參數")
        
        # 獲取更新後的書籤資料
        bookmark = await db_client.get_bookmark(bookmark_id)
        if not bookmark:
            raise HTTPException(status_code=404, detail="書籤不存在")
        
        # 發送更新後的卡片
        from line_bot_service import line_bot_service
        if line_bot_service.enabled:
            flex_card = line_bot_service.create_bookmark_flex_card(bookmark, user_id)
            flex_message = FlexSendMessage(
                alt_text=f"📋 {bookmark.get('title', '更新後的書籤')}",
                contents=flex_card
            )
            
            # 發送 push message
            line_bot_service.line_bot_api.push_message(user_id, flex_message)
            
            return {"status": "success", "message": "卡片已發送"}
        else:
            return {"status": "disabled", "message": "LINE Bot 未啟用"}
        
    except Exception as e:
        logger.error(f"❌ 發送更新卡片失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))
'''
    
    # 在 LINE Bot Webhook 之前插入新端點
    insert_position = content.find('# ==================== LINE Bot Webhook ====================')
    if insert_position != -1:
        new_content = content[:insert_position] + new_endpoint + '\n' + content[insert_position:]
        
        # 寫回文件
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ 後端 API 端點添加完成！")
    else:
        print("❌ 未找到插入位置，請手動添加")

def apply_frontend_fix():
    """應用前端修復"""
    print("🔧 正在修復前端編輯頁面...")
    
    # 讀取原始文件
    with open('frontend/src/EditCard.jsx', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否已經有 showCreateFolder 狀態
    if 'showCreateFolder' not in content:
        # 在 useState 聲明後添加新狀態
        useState_pattern = r'(const \[.*?\] = useState\(.*?\);)'
        new_states = '''  const [showCreateFolder, setShowCreateFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');'''
        
        # 找到最後一個 useState 聲明
        matches = list(re.finditer(useState_pattern, content))
        if matches:
            last_match = matches[-1]
            insert_pos = last_match.end()
            new_content = content[:insert_pos] + '\n' + new_states + content[insert_pos:]
            
            # 寫回文件
            with open('frontend/src/EditCard.jsx', 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ 前端狀態添加完成！")
        else:
            print("❌ 未找到 useState 聲明位置")
    else:
        print("✅ 前端狀態已存在，跳過修復")

if __name__ == "__main__":
    print("🚀 開始應用 BriefCard 智能修復...")
    print("=" * 50)
    
    try:
        apply_line_bot_fix()
        print()
        apply_backend_api_fix()
        print()
        apply_frontend_fix()
        print()
        print("=" * 50)
        print("🎉 所有修復應用完成！")
        print("📋 修復內容：")
        print("   ✅ LINE Bot 即時回饋與自動創建預設資料夾")
        print("   ✅ 後端 API 發送更新卡片端點")
        print("   ✅ 前端編輯頁面狀態改善")
        print()
        print("🔄 請重新部署服務以應用修復")
        
    except Exception as e:
        print(f"❌ 修復過程中發生錯誤: {e}")
