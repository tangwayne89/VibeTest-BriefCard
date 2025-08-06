    def _handle_save_bookmark(self, event: PostbackEvent, bookmark_id: str, user_id: str):
        """處理保存書籤到預設資料夾 - 改善版"""
        logger.info(f"💾 處理保存書籤請求: {bookmark_id} (用戶: {user_id})")
        
        # 立即發送回饋訊息 (解決問題 3-1: 即時回饋)
        self._reply_message(event.reply_token, "📋 正在保存書籤，請稍候...")
        
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
