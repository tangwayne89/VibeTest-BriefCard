#!/usr/bin/env python3
"""
BriefCard PoC - FastAPI 主應用
整合 Supabase、Crawl4AI 和 DeepSeek 的 REST API 服務
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
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
    CreateBookmarkRequest, UpdateBookmarkRequest, CrawlUrlRequest,
    BookmarkResponse, BookmarkListResponse, CrawlResult, AIAnalysisResult,
    HealthCheckResponse, ErrorResponse, SuccessResponse,
    create_error_response, create_success_response
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
    title="BriefCard PoC API",
    description="將任何連結轉換為豐富視覺預覽卡片的 LINE Bot 後端服務",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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

# ==================== 爬蟲相關 API ====================

@app.post("/api/crawl", response_model=CrawlResult)
async def crawl_url(request: CrawlUrlRequest):
    """爬取網址內容（測試用）"""
    try:
        result = await crawler_service.extract_content(str(request.url))
        
        if not result:
            raise HTTPException(
                status_code=400,
                detail="爬取失敗，請檢查網址是否有效"
            )
        
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

@app.get("/api/bookmarks", response_model=BookmarkListResponse)
async def get_bookmarks(
    user_id: Optional[str] = "anonymous",
    page: int = 1,
    page_size: int = 50
):
    """獲取書籤列表"""
    try:
        if not user_id:
            user_id = "anonymous"
        
        bookmarks = await db_client.get_bookmarks_by_user(user_id, page_size)
        
        return BookmarkListResponse(
            bookmarks=[BookmarkResponse(**bookmark) for bookmark in bookmarks],
            total=len(bookmarks),
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"❌ 獲取書籤列表異常: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/bookmarks/{bookmark_id}", response_model=BookmarkResponse)
async def update_bookmark(bookmark_id: str, request: UpdateBookmarkRequest):
    """更新書籤"""
    try:
        # 檢查書籤是否存在
        existing = await db_client.get_bookmark(bookmark_id)
        if not existing:
            raise HTTPException(status_code=404, detail="書籤不存在")
        
        # 準備更新資料
        update_data = {}
        if request.title is not None:
            update_data["title"] = request.title
        if request.tags is not None:
            update_data["tags"] = request.tags
        
        if not update_data:
            return BookmarkResponse(**existing)
        
        result = await db_client.update_bookmark(bookmark_id, update_data)
        
        if not result:
            raise HTTPException(status_code=500, detail="更新書籤失敗")
        
        return BookmarkResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 更新書籤異常: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/bookmarks/{bookmark_id}", response_model=SuccessResponse)
async def delete_bookmark(bookmark_id: str):
    """删除書籤"""
    try:
        # 檢查書籤是否存在
        existing = await db_client.get_bookmark(bookmark_id)
        if not existing:
            raise HTTPException(status_code=404, detail="書籤不存在")
        
        success = await db_client.delete_bookmark(bookmark_id)
        
        if not success:
            raise HTTPException(status_code=500, detail="删除書籤失敗")
        
        return create_success_response("書籤已成功删除")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 删除書籤異常: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 錯誤處理 ====================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """404 錯誤處理"""
    return JSONResponse(
        status_code=404,
        content=create_error_response(
            "NOT_FOUND",
            "請求的資源不存在"
        ).dict()
    )

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

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """500 錯誤處理"""
    logger.error(f"內部伺服器錯誤: {exc}")
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            "INTERNAL_ERROR",
            "內部伺服器錯誤，請稍後再試"
        ).dict()
    )

# ==================== 應用啟動 ====================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )