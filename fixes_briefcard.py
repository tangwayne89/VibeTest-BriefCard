#!/usr/bin/env python3
"""
BriefCard 智能修復方案
包含所有用戶體驗改善的代碼修復
"""

# ==================== 修復 1: LINE Bot 服務改善 ====================

LINE_BOT_SAVE_BOOKMARK_FIX = '''
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
'''

# ==================== 修復 2: 後端 API 新增端點 ====================

BACKEND_API_ENDPOINTS = '''
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
                alt_text=f"�� {bookmark.get('title', '更新後的書籤')}",
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

# ==================== 修復 3: 前端編輯頁面改善 ====================

FRONTEND_EDITCARD_IMPROVEMENTS = '''
// 在 EditCard 組件中添加狀態
const [showCreateFolder, setShowCreateFolder] = useState(false);
const [newFolderName, setNewFolderName] = useState('');

// 創建新資料夾的函數 (解決問題 2: 創建資料夾功能)
const handleCreateFolder = async () => {
  if (!newFolderName.trim()) return;
  
  try {
    const response = await axios.post(
      `${APP_CONFIG.API_BASE_URL}/api/folders`,
      {
        user_id: profile?.userId,
        name: newFolderName.trim(),
        color: '#1976D2',
        is_default: false,
        sort_order: folders.length
      }
    );
    
    // 更新資料夾列表
    const newFolder = response.data;
    setFolders(prev => [...prev, newFolder]);
    
    // 自動選擇新創建的資料夾
    setFormData(prev => ({
      ...prev,
      folder_id: newFolder.id
    }));
    
    // 重置狀態
    setNewFolderName('');
    setShowCreateFolder(false);
    
    alert('✅ 資料夾創建成功！');
  } catch (err) {
    console.error('創建資料夾失敗:', err);
    alert('❌ 創建資料夾失敗，請重試');
  }
};

// 修改保存函數，添加跳轉回 LINE 功能 (解決問題 1: 編輯後跳轉)
const handleSave = async () => {
  if (!bookmark) return;
  
  setIsSaving(true);
  try {
    // 保存書籤
    await axios.patch(
      `${APP_CONFIG.API_BASE_URL}/api/bookmarks/${bookmark.id}`,
      {
        title: formData.title,
        folder_id: formData.folder_id || null,
        notes: formData.notes
      }
    );

    // 通知後端發送更新後的卡片
    await axios.post(
      `${APP_CONFIG.API_BASE_URL}/api/send-updated-card`,
      {
        bookmark_id: bookmark.id,
        user_id: profile?.userId
      }
    );

    alert('✅ 儲存成功！正在跳轉回 LINE...');
    
    // 嘗試跳轉回 LINE
    setTimeout(() => {
      if (window.liff && window.liff.isInClient()) {
        window.liff.closeWindow();
      } else {
        // 如果不在 LINE 內，顯示提示
        alert('請返回 LINE 查看更新後的卡片');
        window.close();
      }
    }, 1500);
    
  } catch (err) {
    console.error('儲存失敗:', err);
    alert('❌ 儲存失敗，請重試');
  } finally {
    setIsSaving(false);
  }
};

// 在資料夾選擇區域添加創建按鈕的 JSX (解決問題 2: 創建資料夾功能)
const folderSectionJSX = `
<div className="card mb-6">
  <div className="flex items-center justify-between mb-3">
    <div className="flex items-center">
      <Folder className="h-5 w-5 text-gray-600 mr-2" />
      <h2 className="text-lg font-medium text-gray-800">資料夾</h2>
    </div>
    <button 
      onClick={() => setShowCreateFolder(true)}
      className="text-sm text-line-green hover:text-line-green-dark flex items-center"
    >
      <Plus className="h-4 w-4 mr-1" />
      新增
    </button>
  </div>
  
  <select
    value={formData.folder_id}
    onChange={(e) => handleInputChange('folder_id', e.target.value)}
    className="input-field mb-3"
  >
    <option value="">選擇資料夾...</option>
    {folders.map(folder => (
      <option key={folder.id} value={folder.id}>
        {folder.name}
      </option>
    ))}
  </select>
  
  {/* 創建資料夾輸入框 */}
  {showCreateFolder && (
    <div className="flex gap-2">
      <input
        type="text"
        value={newFolderName}
        onChange={(e) => setNewFolderName(e.target.value)}
        placeholder="輸入資料夾名稱..."
        className="input-field flex-1"
        onKeyPress={(e) => e.key === 'Enter' && handleCreateFolder()}
      />
      <button 
        onClick={handleCreateFolder}
        className="btn-primary px-3"
      >
        建立
      </button>
      <button 
        onClick={() => {
          setShowCreateFolder(false);
          setNewFolderName('');
        }}
        className="btn-secondary px-3"
      >
        取消
      </button>
    </div>
  )}
</div>
`;
'''

print("🎯 BriefCard 智能修復方案已準備完成！")
print("📋 包含以下修復：")
print("   1. LINE Bot 保存書籤即時回饋與自動創建預設資料夾")
print("   2. 後端 API 發送更新卡片端點")
print("   3. 前端編輯頁面創建資料夾功能與跳轉改善")
print("🚀 準備開始實施...")
