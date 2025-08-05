#!/usr/bin/env python3
"""
BriefCard - Supabase 資料庫客戶端
處理所有資料庫操作和連線管理
"""

from supabase import create_client, Client
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

from config import settings

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Supabase 資料庫客戶端封裝"""
    
    def __init__(self):
        """初始化 Supabase 客戶端"""
        self.client: Optional[Client] = None
        self.connect()
    
    def connect(self) -> bool:
        """建立 Supabase 連線"""
        try:
            self.client = create_client(
                settings.supabase_url,
                settings.supabase_anon_key
            )
            logger.info("✅ Supabase 連線成功")
            return True
        except Exception as e:
            logger.error(f"❌ Supabase 連線失敗: {e}")
            return False
    
    def health_check(self) -> bool:
        """檢查資料庫連線狀態"""
        try:
            if not self.client:
                return False
            
            # 簡單查詢測試連線
            result = self.client.table("bookmarks").select("count").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"資料庫健康檢查失敗: {e}")
            return False
    
    # ==================== 書籤相關操作 ====================
    
    async def create_bookmark(self, bookmark_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """建立新書籤"""
        try:
            result = self.client.table("bookmarks").insert(bookmark_data).execute()
            if result.data:
                logger.info(f"✅ 書籤建立成功: {result.data[0]['id']}")
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"❌ 建立書籤失敗: {e}")
            return None
    
    async def get_bookmark(self, bookmark_id: str) -> Optional[Dict[str, Any]]:
        """根據 ID 獲取書籤"""
        try:
            result = self.client.table("bookmarks").select("*").eq("id", bookmark_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"❌ 獲取書籤失敗: {e}")
            return None
    
    async def get_bookmarks_by_user(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """獲取用戶的所有書籤"""
        try:
            result = (self.client.table("bookmarks")
                     .select("*")
                     .eq("user_id", user_id)
                     .order("created_at", desc=True)
                     .limit(limit)
                     .execute())
            return result.data or []
        except Exception as e:
            logger.error(f"❌ 獲取用戶書籤失敗: {e}")
            return []
    
    async def update_bookmark(self, bookmark_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新書籤資訊"""
        try:
            update_data["updated_at"] = datetime.utcnow().isoformat()
            result = (self.client.table("bookmarks")
                     .update(update_data)
                     .eq("id", bookmark_id)
                     .execute())
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"❌ 更新書籤失敗: {e}")
            return None
    
    async def delete_bookmark(self, bookmark_id: str) -> bool:
        """删除書籤"""
        try:
            result = self.client.table("bookmarks").delete().eq("id", bookmark_id).execute()
            logger.info(f"✅ 書籤删除成功: {bookmark_id}")
            return True
        except Exception as e:
            logger.error(f"❌ 删除書籤失敗: {e}")
            return False
    
    # ==================== 分享相關操作 ====================
    
    async def create_share(self, bookmark_id: str, share_token: str) -> Optional[Dict[str, Any]]:
        """建立分享連結"""
        try:
            share_data = {
                "bookmark_id": bookmark_id,
                "share_token": share_token,
                "created_at": datetime.utcnow().isoformat()
            }
            result = self.client.table("shares").insert(share_data).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"❌ 建立分享連結失敗: {e}")
            return None
    
    async def get_share_by_token(self, share_token: str) -> Optional[Dict[str, Any]]:
        """根據分享 token 獲取分享資訊"""
        try:
            result = (self.client.table("shares")
                     .select("*, bookmarks(*)")
                     .eq("share_token", share_token)
                     .execute())
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"❌ 獲取分享資訊失敗: {e}")
            return None
    
    # ==================== 資料夾相關操作 ====================
    
    async def create_folder(self, folder_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """建立新資料夾"""
        try:
            result = self.client.table("folders").insert(folder_data).execute()
            if result.data:
                logger.info(f"✅ 資料夾建立成功: {result.data[0]['id']}")
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"❌ 建立資料夾失敗: {e}")
            return None
    
    async def get_folder(self, folder_id: str) -> Optional[Dict[str, Any]]:
        """根據 ID 獲取資料夾"""
        try:
            result = self.client.table("folders").select("*").eq("id", folder_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"❌ 獲取資料夾失敗: {e}")
            return None
    
    async def get_folders_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """獲取用戶的所有資料夾"""
        try:
            result = (self.client.table("folders")
                     .select("*")
                     .eq("user_id", user_id)
                     .order("sort_order", desc=False)
                     .order("created_at", desc=False)
                     .execute())
            return result.data or []
        except Exception as e:
            logger.error(f"❌ 獲取用戶資料夾失敗: {e}")
            return []
    
    async def get_default_folder(self, user_id: str) -> Optional[Dict[str, Any]]:
        """獲取用戶的預設資料夾"""
        try:
            result = (self.client.table("folders")
                     .select("*")
                     .eq("user_id", user_id)
                     .eq("is_default", True)
                     .limit(1)
                     .execute())
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"❌ 獲取預設資料夾失敗: {e}")
            return None
    
    async def update_folder(self, folder_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新資料夾資訊"""
        try:
            result = (self.client.table("folders")
                     .update(update_data)
                     .eq("id", folder_id)
                     .execute())
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"❌ 更新資料夾失敗: {e}")
            return None
    
    async def delete_folder(self, folder_id: str) -> bool:
        """删除資料夾"""
        try:
            result = self.client.table("folders").delete().eq("id", folder_id).execute()
            logger.info(f"✅ 資料夾删除成功: {folder_id}")
            return True
        except Exception as e:
            logger.error(f"❌ 删除資料夾失敗: {e}")
            return False
    
    async def get_bookmarks_by_folder(self, folder_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """獲取資料夾內的書籤"""
        try:
            result = (self.client.table("bookmarks")
                     .select("*")
                     .eq("folder_id", folder_id)
                     .order("created_at", desc=True)
                     .limit(limit)
                     .execute())
            return result.data or []
        except Exception as e:
            logger.error(f"❌ 獲取資料夾書籤失敗: {e}")
            return []

# 建立全域資料庫客戶端實例
db_client = SupabaseClient()

# 測試連線
if __name__ == "__main__":
    print("🗄️ Supabase 資料庫連線測試")
    if db_client.health_check():
        print("✅ 資料庫連線正常")
    else:
        print("❌ 資料庫連線失敗")