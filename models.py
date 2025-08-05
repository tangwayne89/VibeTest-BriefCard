#!/usr/bin/env python3
"""
BriefCard - Pydantic 資料模型
定義 API 請求和回應的資料結構
"""

from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# ==================== 基礎模型 ====================

class BookmarkStatus(str, Enum):
    """書籤狀態"""
    PROCESSING = "processing"  # 處理中
    COMPLETED = "completed"    # 完成
    FAILED = "failed"         # 失敗

class ContentCategory(str, Enum):
    """內容分類"""
    TECH = "技術/科技"
    NEWS = "新聞時事"
    BUSINESS = "商業財經"
    ENTERTAINMENT = "娛樂休閒"
    EDUCATION = "教育學習"
    HEALTH = "健康醫療"
    LIFESTYLE = "生活資訊"
    SOCIAL = "社群媒體"
    SHOPPING = "購物消費"
    TOOLS = "工具軟體"
    OTHER = "其他"

# ==================== 請求模型 ====================

class CreateBookmarkRequest(BaseModel):
    """建立書籤請求"""
    url: HttpUrl = Field(..., description="要收藏的網址")
    user_id: Optional[str] = Field(None, description="用戶 ID（臨時用於測試）")
    folder_id: Optional[str] = Field(None, description="資料夾 ID（不提供則使用預設資料夾）")
    notes: Optional[str] = Field(None, description="個人筆記")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/article",
                "user_id": "test-user-123",
                "folder_id": "folder-uuid-123",
                "notes": "這是一篇有趣的文章"
            }
        }

class UpdateBookmarkRequest(BaseModel):
    """更新書籤請求"""
    title: Optional[str] = Field(None, description="自訂標題")
    tags: Optional[List[str]] = Field(None, description="標籤列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "我的自訂標題",
                "tags": ["重要", "待讀"]
            }
        }

class CrawlUrlRequest(BaseModel):
    """爬取網址請求"""
    url: HttpUrl = Field(..., description="要爬取的網址")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/article"
            }
        }

# ==================== 回應模型 ====================

class CrawlResult(BaseModel):
    """爬取結果"""
    url: str = Field(..., description="原始網址")
    title: str = Field("", description="網頁標題")
    description: str = Field("", description="網頁描述")
    image_url: str = Field("", description="主要圖片 URL")
    content_markdown: str = Field("", description="Markdown 格式內容")
    content_text: str = Field("", description="純文字內容")
    author: str = Field("", description="作者")
    publish_date: str = Field("", description="發布日期")
    site_name: str = Field("", description="網站名稱")
    crawl_duration: float = Field(0.0, description="爬取耗時（秒）")
    word_count: int = Field(0, description="字數統計")
    status_code: int = Field(200, description="HTTP 狀態碼")
    success: bool = Field(True, description="是否成功")
    error: Optional[str] = Field(None, description="錯誤訊息")

class AIAnalysisResult(BaseModel):
    """AI 分析結果"""
    summary: Optional[str] = Field(None, description="內容摘要")
    keywords: List[str] = Field(default_factory=list, description="關鍵詞列表")
    category: str = Field("其他", description="內容分類")

class BookmarkResponse(BaseModel):
    """書籤回應"""
    id: str = Field(..., description="書籤 ID")
    user_id: Optional[str] = Field(None, description="用戶 ID")
    folder_id: Optional[str] = Field(None, description="資料夾 ID")
    url: str = Field(..., description="原始網址")
    title: Optional[str] = Field("", description="標題")
    description: Optional[str] = Field("", description="描述")
    image_url: Optional[str] = Field("", description="圖片 URL")
    content_markdown: Optional[str] = Field(None, description="Markdown 內容")
    summary: Optional[str] = Field(None, description="AI 摘要")
    notes: Optional[str] = Field(None, description="個人筆記")
    tags: Optional[List[str]] = Field(default_factory=list, description="標籤")
    category: Optional[str] = Field("其他", description="分類")
    status: Optional[str] = Field("processing", description="處理狀態")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class FolderResponse(BaseModel):
    """資料夾回應"""
    id: str = Field(..., description="資料夾 ID")
    user_id: str = Field(..., description="用戶 ID")
    name: str = Field(..., description="資料夾名稱")
    color: str = Field("#1976D2", description="資料夾顏色")
    is_default: bool = Field(False, description="是否為預設資料夾")
    sort_order: int = Field(0, description="排序順序")
    bookmark_count: int = Field(0, description="書籤數量")
    created_at: datetime = Field(..., description="建立時間")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CreateFolderRequest(BaseModel):
    """建立資料夾請求"""
    name: str = Field(..., description="資料夾名稱", min_length=1, max_length=50)
    color: str = Field("#1976D2", description="資料夾顏色")
    user_id: Optional[str] = Field(None, description="用戶 ID（臨時用於測試）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "工作相關",
                "color": "#FF5722",
                "user_id": "test-user-123"
            }
        }

class UpdateFolderRequest(BaseModel):
    """更新資料夾請求"""
    name: Optional[str] = Field(None, description="資料夾名稱", min_length=1, max_length=50)
    color: Optional[str] = Field(None, description="資料夾顏色")
    sort_order: Optional[int] = Field(None, description="排序順序")

class BookmarkListResponse(BaseModel):
    """書籤列表回應"""
    bookmarks: List[BookmarkResponse] = Field(..., description="書籤列表")
    total: int = Field(..., description="總數量")
    page: int = Field(1, description="頁碼")
    page_size: int = Field(50, description="每頁數量")

class FolderListResponse(BaseModel):
    """資料夾列表回應"""
    folders: List[FolderResponse] = Field(..., description="資料夾列表")
    total: int = Field(..., description="總數量")

class ShareResponse(BaseModel):
    """分享回應"""
    share_id: str = Field(..., description="分享 ID")
    share_token: str = Field(..., description="分享 token")
    share_url: str = Field(..., description="分享網址")
    bookmark: BookmarkResponse = Field(..., description="書籤資訊")
    created_at: datetime = Field(..., description="建立時間")

# ==================== 錯誤回應模型 ====================

class ErrorResponse(BaseModel):
    """錯誤回應"""
    error: str = Field(..., description="錯誤類型")
    message: str = Field(..., description="錯誤訊息")
    details: Optional[Dict[str, Any]] = Field(None, description="詳細資訊")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "INVALID_URL",
                "message": "提供的網址格式不正確",
                "details": {"url": "invalid-url"}
            }
        }

class SuccessResponse(BaseModel):
    """成功回應"""
    success: bool = Field(True, description="是否成功")
    message: str = Field(..., description="成功訊息")
    data: Optional[Dict[str, Any]] = Field(None, description="附加資料")

# ==================== 健康檢查模型 ====================

class HealthCheckResponse(BaseModel):
    """健康檢查回應"""
    status: str = Field(..., description="服務狀態")
    timestamp: datetime = Field(..., description="檢查時間")
    version: str = Field("1.0.0", description="API 版本")
    services: Dict[str, Any] = Field(..., description="各服務狀態")  # 改為 Any 以支援更複雜的狀態資訊
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-01T00:00:00Z",
                "version": "1.0.0",
                "services": {
                    "database": True,
                    "crawler": True,
                    "ai_service": True,
                    "ai_provider": "openrouter",
                    "ai_providers": {
                        "openrouter": True,
                        "deepseek": False,
                        "mock": True
                    }
                }
            }
        }

# ==================== LINE Bot 相關模型 ====================

class LineMessageEvent(BaseModel):
    """LINE 訊息事件"""
    type: str = Field(..., description="事件類型")
    message: Dict[str, Any] = Field(..., description="訊息內容")
    source: Dict[str, Any] = Field(..., description="訊息來源")
    timestamp: int = Field(..., description="時間戳記")
    
class LineFlexMessage(BaseModel):
    """LINE Flex 訊息"""
    type: str = Field("flex", description="訊息類型")
    altText: str = Field(..., description="替代文字")
    contents: Dict[str, Any] = Field(..., description="Flex 內容")

# ==================== 工具函數 ====================

def create_error_response(error_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> ErrorResponse:
    """建立錯誤回應"""
    return ErrorResponse(
        error=error_type,
        message=message,
        details=details
    )

def create_success_response(message: str, data: Optional[Dict[str, Any]] = None) -> SuccessResponse:
    """建立成功回應"""
    return SuccessResponse(
        success=True,
        message=message,
        data=data
    )