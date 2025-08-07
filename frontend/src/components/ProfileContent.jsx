import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  User, 
  Bell, 
  Settings,
  BarChart3,
  Download,
  Shield,
  HelpCircle,
  ExternalLink,
  Loader2,
  Check
} from 'lucide-react';
import { initLIFF, getLiffProfile, getWebParams, APP_CONFIG } from '../liff';

const ProfileContent = () => {
  const [profile, setProfile] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // 設定狀態
  const [settings, setSettings] = useState({
    notifications: {
      daily_reminder: true,
      reminder_time: '21:00',
      new_features: true,
      weekly_summary: false
    },
    preferences: {
      language: 'zh-TW',
      timezone: 'Asia/Taipei',
      theme: 'light',
      default_view: 'grid'
    },
    privacy: {
      analytics: true,
      usage_data: true
    }
  });

  // 初始化
  useEffect(() => {
    const initialize = async () => {
      try {
        await initLIFF();
        const userProfile = await getLiffProfile();
        const { userId } = getWebParams();
        const finalUserId = userId || userProfile?.userId || 'test-user';
        
        setProfile({ 
          ...userProfile, 
          userId: finalUserId,
          displayName: userProfile?.displayName || '用戶'
        });
        
        await loadStats(finalUserId);
      } catch (error) {
        console.error('初始化失敗:', error);
        setProfile({ userId: 'test-user', displayName: '用戶' });
        await loadStats('test-user');
      } finally {
        setLoading(false);
      }
    };

    initialize();
  }, []);

  // 載入統計資料
  const loadStats = async (userId) => {
    try {
      const response = await axios.get(
        `${APP_CONFIG.API_BASE_URL}/api/v1/bookmarks/stats?user_id=${userId}`
      );
      setStats(response.data.statistics);
    } catch (error) {
      console.error('載入統計失敗:', error);
      setStats({ total: 0, today: 0, this_week: 0, this_month: 0 });
    }
  };

  // 保存設定
  const saveSettings = async () => {
    setSaving(true);
    try {
      // 這裡可以調用 API 保存設定
      // await axios.put(`${APP_CONFIG.API_BASE_URL}/api/user/settings`, settings);
      
      // 模擬保存延遲
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      alert('✅ 設定已保存');
    } catch (error) {
      console.error('保存設定失敗:', error);
      alert('❌ 保存設定失敗，請重試');
    } finally {
      setSaving(false);
    }
  };

  // 導出數據
  const exportData = async () => {
    try {
      alert('🚀 數據導出功能即將推出！');
      // 實際實作時可以調用 API 導出數據
    } catch (error) {
      console.error('導出數據失敗:', error);
      alert('❌ 導出數據失敗，請重試');
    }
  };

  // 更新設定
  const updateSetting = (category, key, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">載入中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* 頁面標題和操作 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <User className="h-6 w-6 text-blue-600" />
          <h1 className="text-2xl font-bold text-gray-900">個人設定</h1>
        </div>
        
        <button
          onClick={saveSettings}
          disabled={saving}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
          <span>保存設定</span>
        </button>
      </div>

      {/* 用戶資訊卡片 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
            <User className="h-8 w-8 text-blue-600" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">{profile?.displayName}</h2>
            <p className="text-gray-500">LINE ID: {profile?.userId}</p>
          </div>
        </div>
        
        {/* 使用統計 */}
        {stats && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3">📊 使用統計</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="text-center p-3 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
                <div className="text-xl font-bold text-blue-600">{stats.total}</div>
                <div className="text-xs text-blue-700">總書籤數</div>
              </div>
              <div className="text-center p-3 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
                <div className="text-xl font-bold text-green-600">{stats.today}</div>
                <div className="text-xs text-green-700">今日新增</div>
              </div>
              <div className="text-center p-3 bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg">
                <div className="text-xl font-bold text-orange-600">{stats.this_week}</div>
                <div className="text-xs text-orange-700">本週新增</div>
              </div>
              <div className="text-center p-3 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
                <div className="text-xl font-bold text-purple-600">{stats.this_month}</div>
                <div className="text-xs text-purple-700">本月新增</div>
              </div>
            </div>
            
            {/* 使用趨勢提示 */}
            <div className="mt-3 p-2 bg-gray-50 rounded-md">
              <p className="text-xs text-gray-600">
                🎯 {stats.today > 0 ? `今天已新增 ${stats.today} 個書籤，保持好習慣！` : '今天還沒有新增書籤，來收藏一些有趣的內容吧！'}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* 通知設定 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Bell className="h-5 w-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">通知設定</h3>
        </div>
        
        <div className="space-y-6">
          {/* 每日提醒主選項 */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="font-medium text-gray-900">每日提醒</div>
                <div className="text-sm text-gray-500">每天提醒您閱讀保存的書籤</div>
              </div>
              <input
                type="checkbox"
                checked={settings.notifications.daily_reminder}
                onChange={(e) => updateSetting('notifications', 'daily_reminder', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
            </div>
            
            {/* 提醒時間子選項 - 只有啟用每日提醒時才顯示 */}
            {settings.notifications.daily_reminder && (
              <div className="ml-4 pt-3 border-t border-gray-100">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-gray-700 text-sm">⏰ 提醒時間</div>
                    <div className="text-xs text-gray-500">選擇每日推送書籤的時間</div>
                  </div>
                  <input
                    type="time"
                    value={settings.notifications.reminder_time}
                    onChange={(e) => updateSetting('notifications', 'reminder_time', e.target.value)}
                    className="px-3 py-1 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                {/* 時間說明 */}
                <div className="mt-2 p-2 bg-blue-50 rounded-md">
                  <p className="text-xs text-blue-700">
                    💡 系統會在您設定的時間推送未讀書籤，幫助您養成閱讀習慣
                  </p>
                </div>
              </div>
            )}
          </div>
          
          {/* 其他通知選項 */}
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-gray-900">新功能通知</div>
              <div className="text-sm text-gray-500">接收新功能和更新通知</div>
            </div>
            <input
              type="checkbox"
              checked={settings.notifications.new_features}
              onChange={(e) => updateSetting('notifications', 'new_features', e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-gray-900">週報摘要</div>
              <div className="text-sm text-gray-500">每週發送使用摘要報告</div>
            </div>
            <input
              type="checkbox"
              checked={settings.notifications.weekly_summary}
              onChange={(e) => updateSetting('notifications', 'weekly_summary', e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
          </div>
        </div>
      </div>

      {/* 偏好設定 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Settings className="h-5 w-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">偏好設定</h3>
        </div>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-gray-900">語言</div>
              <div className="text-sm text-gray-500">選擇介面語言</div>
            </div>
            <select
              value={settings.preferences.language}
              onChange={(e) => updateSetting('preferences', 'language', e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="zh-TW">繁體中文</option>
              <option value="zh-CN">简体中文</option>
              <option value="en">English</option>
              <option value="ja">日本語</option>
            </select>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-gray-900">時區</div>
              <div className="text-sm text-gray-500">設定您的時區</div>
            </div>
            <select
              value={settings.preferences.timezone}
              onChange={(e) => updateSetting('preferences', 'timezone', e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="Asia/Taipei">台北 (UTC+8)</option>
              <option value="Asia/Tokyo">東京 (UTC+9)</option>
              <option value="Asia/Shanghai">上海 (UTC+8)</option>
              <option value="UTC">UTC (UTC+0)</option>
            </select>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-gray-900">預設檢視</div>
              <div className="text-sm text-gray-500">書籤列表的預設顯示方式</div>
            </div>
            <select
              value={settings.preferences.default_view}
              onChange={(e) => updateSetting('preferences', 'default_view', e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="grid">網格檢視</option>
              <option value="list">列表檢視</option>
            </select>
          </div>
        </div>
      </div>

      {/* 隱私設定 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="h-5 w-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">隱私設定</h3>
        </div>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-gray-900">分析資料</div>
              <div className="text-sm text-gray-500">允許收集匿名使用分析資料</div>
            </div>
            <input
              type="checkbox"
              checked={settings.privacy.analytics}
              onChange={(e) => updateSetting('privacy', 'analytics', e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-gray-900">使用資料</div>
              <div className="text-sm text-gray-500">分享使用資料以改善服務品質</div>
            </div>
            <input
              type="checkbox"
              checked={settings.privacy.usage_data}
              onChange={(e) => updateSetting('privacy', 'usage_data', e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
          </div>
        </div>
      </div>

      {/* 數據管理 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="h-5 w-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">數據管理</h3>
        </div>
        
        <div className="space-y-3">
          <button
            onClick={exportData}
            className="w-full flex items-center justify-between p-3 text-left border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <Download className="h-5 w-5 text-gray-600" />
              <div>
                <div className="font-medium text-gray-900">導出數據</div>
                <div className="text-sm text-gray-500">下載您的所有書籤資料</div>
              </div>
            </div>
            <ExternalLink className="h-4 w-4 text-gray-400" />
          </button>
          
          <button className="w-full flex items-center justify-between p-3 text-left border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <div className="flex items-center gap-3">
              <BarChart3 className="h-5 w-5 text-gray-600" />
              <div>
                <div className="font-medium text-gray-900">使用統計</div>
                <div className="text-sm text-gray-500">查看詳細的使用分析</div>
              </div>
            </div>
            <ExternalLink className="h-4 w-4 text-gray-400" />
          </button>
        </div>
      </div>

      {/* 幫助與支援 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <HelpCircle className="h-5 w-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">幫助與支援</h3>
        </div>
        
        <div className="space-y-3">
          <button className="w-full flex items-center justify-between p-3 text-left border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <div>
              <div className="font-medium text-gray-900">使用說明</div>
              <div className="text-sm text-gray-500">了解如何使用 BriefCard</div>
            </div>
            <ExternalLink className="h-4 w-4 text-gray-400" />
          </button>
          
          <button className="w-full flex items-center justify-between p-3 text-left border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <div>
              <div className="font-medium text-gray-900">意見反饋</div>
              <div className="text-sm text-gray-500">向我們提供建議或回報問題</div>
            </div>
            <ExternalLink className="h-4 w-4 text-gray-400" />
          </button>
          
          <div className="pt-3 border-t border-gray-200">
            <div className="text-sm text-gray-500">
              BriefCard v1.0.0 | 
              <a href="#" className="text-blue-600 hover:text-blue-700 ml-1">隱私政策</a> | 
              <a href="#" className="text-blue-600 hover:text-blue-700 ml-1">服務條款</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileContent;