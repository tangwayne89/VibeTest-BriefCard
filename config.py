#!/usr/bin/env python3
"""
BriefCard - 配置管理
集中管理所有環境變數和應用配置
"""

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional

# 載入環境變數
load_dotenv()

class Settings(BaseSettings):
    """應用配置類"""
    
    # 應用基本設定
    app_env: str = os.getenv("APP_ENV", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # Supabase 配置
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    
    # AI 服務配置
    ai_service_provider: str = os.getenv("AI_SERVICE_PROVIDER", "openrouter")  # openrouter, deepseek, openai
    
    # DeepSeek API 配置
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    
    # OpenRouter API 配置
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.2-3b-instruct:free")
    
    # LINE Bot 配置
    line_channel_access_token: Optional[str] = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    line_channel_secret: Optional[str] = os.getenv("LINE_CHANNEL_SECRET")
    
    # 爬蟲設定
    crawler_timeout: int = int(os.getenv("CRAWLER_TIMEOUT", "30"))
    max_content_length: int = int(os.getenv("MAX_CONTENT_LENGTH", "50000"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def validate_required_settings(self) -> bool:
        """驗證必要的設定是否完整"""
        # 基本必要設定
        required_fields = [
            ("Supabase URL", self.supabase_url),
            ("Supabase Anon Key", self.supabase_anon_key),
        ]
        
        # 根據 AI 服務提供者檢查對應的 API Key
        if self.ai_service_provider == "deepseek":
            required_fields.append(("DeepSeek API Key", self.deepseek_api_key))
        elif self.ai_service_provider == "openrouter":
            required_fields.append(("OpenRouter API Key", self.openrouter_api_key))
        elif self.ai_service_provider == "mock":
            # 模擬服務不需要 API Key
            pass
        
        missing_fields = []
        for field_name, value in required_fields:
            if not value:
                missing_fields.append(field_name)
        
        if missing_fields:
            print(f"❌ 缺少必要配置: {', '.join(missing_fields)}")
            return False
        
        print(f"✅ 所有必要配置已設定 (AI服務: {self.ai_service_provider})")
        return True

# 建立全域設定實例
settings = Settings()

# 驗證設定
if __name__ == "__main__":
    print("🔧 BriefCard 配置檢查")
    print(f"環境: {settings.app_env}")
    print(f"除錯模式: {settings.debug}")
    print(f"伺服器: {settings.host}:{settings.port}")
    print()
    settings.validate_required_settings()