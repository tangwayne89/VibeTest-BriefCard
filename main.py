#!/usr/bin/env python3
"""
BriefCard - LINE Bot 後端服務
將任何連結轉換為豐富視覺預覽卡片的智能服務
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

# 本地模組
from config import settings
from database import db_client
from crawler_service import crawler_service
from ai_service_factory import ai_service
from line_bot_service import line_bot_service
from models import (
    CreateBookmarkRequest, CrawlUrlRequest,
    BookmarkResponse, CrawlResult,
    HealthCheckResponse, SuccessResponse,
    create_success_response
)

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== 生命週期管理 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動時
    logger.info("🚀 BriefCard PoC API 正在啟動...")
    
    # 驗證配置
    if not settings.validate_required_settings():
        logger.error("❌ 配置驗證失敗，應用無法啟動")
        exit(1)
    
    # 檢查服務連線
    services_status = await check_services_health()
    failed_services = [name for name, status in services_status.items() if not status]
    
    if failed_services:
        logger.warning(f"⚠️ 部分服務連線失敗: {failed_services}")
    else:
        logger.info("✅ 所有服務連線正常")
    
    logger.info(f"🌟 BriefCard PoC API 已啟動 - {settings.host}:{settings.port}")
    
    yield
    
    # 關閉時
    logger.info("🛑 BriefCard PoC API 正在關閉...")
    await ai_service.close()
    logger.info("✅ 應用已安全關閉")

# ==================== 應用初始化 ====================

app = FastAPI(
    title="BriefCard API",
    description="智能連結預覽卡片生成服務 - LINE Bot 後端",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,  # 生產環境隱藏文檔
    redoc_url=None,  # 移除 ReDoc
    lifespan=lifespan
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # PoC 階段允許所有來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 工具函數 ====================

async def check_services_health() -> dict:
    """檢查各服務健康狀態"""
    from ai_service_factory import AIServiceFactory
    
    ai_providers = AIServiceFactory.get_available_providers()
    ai_service_available = ai_service is not None and any(ai_providers.values())
    
    return {
        "database": db_client.health_check(),
        "crawler": True,  # Crawl4AI 沒有直接的健康檢查
        "ai_service": ai_service_available,
        "ai_provider": settings.ai_service_provider,
        "ai_providers": ai_providers
    }

async def process_bookmark_content(bookmark_id: str, url: str):
    """背景任務：處理書籤內容（爬取 + AI 分析）"""
    try:
        logger.info(f"📋 開始處理書籤內容: {bookmark_id}")
        
        # 1. 爬取網頁內容
        crawl_result = await crawler_service.extract_content(url)
        
        if not crawl_result or not crawl_result.get("success"):
            error_msg = crawl_result.get("error", "未知爬取錯誤") if crawl_result else "爬蟲服務無回應"
            logger.error(f"❌ 爬取失敗: {bookmark_id} - {error_msg}")
            await db_client.update_bookmark(bookmark_id, {
                "status": "failed",
                "description": f"爬取失敗: {error_msg}"
            })
            return
        
        # 2. AI 分析內容
        ai_analysis = await ai_service.analyze_content(
            crawl_result.get("title", ""),
            crawl_result.get("content_markdown", "")
        )
        
        # 3. 更新書籤資料
        update_data = {
            "title": crawl_result.get("title", ""),
            "description": crawl_result.get("description", ""),
            "image_url": crawl_result.get("image_url", ""),
            "content_markdown": crawl_result.get("content_markdown", ""),
            "summary": ai_analysis.get("summary"),
            "tags": ai_analysis.get("keywords", []),
            "category": ai_analysis.get("category", "其他"),
            "status": "completed"
        }
        
        result = await db_client.update_bookmark(bookmark_id, update_data)
        
        if result:
            logger.info(f"✅ 書籤處理完成: {bookmark_id}")
        else:
            logger.error(f"❌ 更新書籤失敗: {bookmark_id}")
            
    except Exception as e:
        logger.error(f"❌ 處理書籤內容異常: {bookmark_id} - {e}")
        await db_client.update_bookmark(bookmark_id, {"status": "failed"})

# ==================== API 路由 ====================

@app.get("/", response_model=SuccessResponse)
async def root():
    """根路由"""
    return create_success_response(
        message="BriefCard PoC API 正在運行",
        data={
            "version": "1.0.0",
            "environment": settings.app_env,
            "docs": "/docs"
        }
    )

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """健康檢查"""
    services_status = await check_services_health()
    overall_status = "healthy" if all(services_status.values()) else "degraded"
    
    return HealthCheckResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        services=services_status
    )

# ==================== 測試 API（僅開發模式）====================

@app.post("/api/crawl", response_model=CrawlResult)
async def crawl_url(request: CrawlUrlRequest):
    """爬取網址內容（測試用）"""
    if not settings.debug:
        raise HTTPException(status_code=404, detail="Not Found")
    
    try:
        result = await crawler_service.extract_content(str(request.url))
        if not result or not result.get("success"):
            raise HTTPException(status_code=400, detail="爬取失敗，請檢查網址是否有效")
        return CrawlResult(**result)
    except Exception as e:
        logger.error(f"❌ 爬取 API 異常: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 書籤相關 API ====================

@app.post("/api/bookmarks", response_model=BookmarkResponse)
async def create_bookmark(
    request: CreateBookmarkRequest,
    background_tasks: BackgroundTasks
):
    """建立新書籤"""
    try:
        # 建立初始書籤記錄
        bookmark_data = {
            "id": str(uuid.uuid4()),
            "user_id": request.user_id or "anonymous",
            "url": str(request.url),
            "title": "",
            "status": "processing",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = await db_client.create_bookmark(bookmark_data)
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="建立書籤失敗"
            )
        
        # 啟動背景任務處理內容
        background_tasks.add_task(
            process_bookmark_content,
            result["id"],
            str(request.url)
        )
        
        return BookmarkResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ 建立書籤異常: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/bookmarks/{bookmark_id}", response_model=BookmarkResponse)
async def get_bookmark(bookmark_id: str):
    """獲取書籤詳情"""
    try:
        result = await db_client.get_bookmark(bookmark_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="書籤不存在"
            )
        
        return BookmarkResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 獲取書籤異常: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== LIFF API 端點 ====================

@app.patch("/api/bookmarks/{bookmark_id}", response_model=BookmarkResponse)
async def update_bookmark(bookmark_id: str, request: dict):
    """更新書籤資料"""
    try:
        result = await db_client.update_bookmark(bookmark_id, request)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="書籤不存在或更新失敗"
            )
        
        return BookmarkResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 更新書籤異常: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/folders", response_model=dict)
async def get_folders(user_id: str):
    """獲取用戶資料夾列表"""
    try:
        folders = await db_client.get_folders_by_user(user_id)
        
        return {
            "folders": folders,
            "total": len(folders)
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取資料夾列表異常: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/folders", response_model=dict)
async def create_folder(request: dict):
    """建立新資料夾"""
    try:
        folder_data = {
            "id": str(uuid.uuid4()),
            "user_id": request.get("user_id"),
            "name": request.get("name"),
            "color": request.get("color", "#1976D2"),
            "is_default": request.get("is_default", False),
            "sort_order": request.get("sort_order", 0),
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = await db_client.create_folder(folder_data)
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail="建立資料夾失敗"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 建立資料夾異常: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 書籤歷史管理 API ====================

@app.get("/api/v1/bookmarks/history")
async def get_bookmark_history(
    user_id: str,
    page: int = 1,
    limit: int = 20,
    sort_by: str = "created_at",
    order: str = "desc"
):
    """獲取用戶書籤歷史（分頁）"""
    try:
        offset = (page - 1) * limit
        bookmarks = await db_client.get_bookmarks_by_user(user_id, limit, offset)
        
        # 獲取總數用於分頁計算
        stats = await db_client.get_bookmark_stats(user_id)
        total = stats.get("total", 0)
        total_pages = (total + limit - 1) // limit
        
        return {
            "bookmarks": bookmarks,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total,
                "items_per_page": limit,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    except Exception as e:
        logger.error(f"❌ 獲取書籤歷史失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/bookmarks/search")
async def search_bookmarks(user_id: str, q: str, limit: int = 20):
    """搜索用戶書籤"""
    try:
        if not q or len(q.strip()) < 2:
            raise HTTPException(status_code=400, detail="搜索關鍵字至少需要2個字符")
        
        bookmarks = await db_client.search_bookmarks(user_id, q.strip(), limit)
        
        return {
            "query": q,
            "results": bookmarks,
            "count": len(bookmarks)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 搜索書籤失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/bookmarks/stats")
async def get_bookmark_stats(user_id: str):
    """獲取用戶書籤統計資訊"""
    try:
        stats = await db_client.get_bookmark_stats(user_id)
        
        # 添加一些額外的統計資訊
        recent_bookmarks = await db_client.get_bookmarks_by_user(user_id, limit=5)
        
        return {
            "statistics": stats,
            "recent_bookmarks": recent_bookmarks,
            "summary": {
                "growth_today": stats["today"],
                "growth_week": stats["this_week"],
                "growth_month": stats["this_month"],
                "total_saved": stats["total"]
            }
        }
    except Exception as e:
        logger.error(f"❌ 獲取書籤統計失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 內部 API（由 LINE Bot 服務調用）====================
# 其他 CRUD 操作通過內部函數處理，減少公開 API 端點

# ==================== 錯誤處理 ====================
# 簡化錯誤處理，使用 FastAPI 默認行為


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

# ==================== LINE Bot Webhook ====================

@app.post("/webhook/line")
async def line_webhook(request: Request):
    """LINE Bot Webhook 端點"""
    try:
        # 獲取請求內容
        body = await request.body()
        signature = request.headers.get('X-Line-Signature', '')
        
        logger.info(f"📨 收到 LINE webhook: body length={len(body)}, signature={signature[:20]}...")
        
        # 檢查 LINE Bot 服務是否可用
        if not line_bot_service.enabled:
            logger.warning("⚠️ LINE Bot 服務未啟用，但返回 200")
            return JSONResponse(status_code=200, content={"status": "disabled"})
        
        # 處理事件
        try:
            from linebot.exceptions import InvalidSignatureError
            
            # 如果沒有簽名，可能是驗證請求
            if not signature:
                logger.info("✅ 無簽名的驗證請求，直接返回成功")
                return JSONResponse(status_code=200, content={"status": "ok"})
            
            # 使用 handler 處理事件
            line_bot_service.handler.handle(body.decode('utf-8'), signature)
            
            logger.info("✅ LINE webhook 處理成功")
            return JSONResponse(status_code=200, content={"status": "ok"})
            
        except InvalidSignatureError as e:
            logger.error(f"❌ LINE webhook 簽名驗證失敗: {e}")
            # 對於驗證階段，返回 200 而不是 400
            logger.info("🔄 返回 200 以通過 LINE 驗證")
            return JSONResponse(status_code=200, content={"status": "signature_failed_but_ok"})
        except Exception as e:
            logger.error(f"❌ LINE webhook 處理失敗: {e}")
            # 所有錯誤都返回 200 以通過驗證
            return JSONResponse(status_code=200, content={"status": "error_but_ok", "error": str(e)})
            
    except Exception as e:
        logger.error(f"❌ LINE webhook 異常: {e}")
        return JSONResponse(status_code=200, content={"error": "Internal server error"})

# ==================== 異常處理器 ====================
# 使用 FastAPI 默認錯誤處理，簡化代碼

# ==================== 應用啟動 ====================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )