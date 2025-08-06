import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  Folder, 
  User, 
  ArrowLeft,
  Menu,
  X
} from 'lucide-react';
import { initLIFF, getLiffProfile, getWebParams } from './liff';

// 導入三個功能組件
import BookmarkHistory from './components/BookmarkHistory';
import FoldersContent from './components/FoldersContent';
import ProfileContent from './components/ProfileContent';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('bookmarks');
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // 初始化
  useEffect(() => {
    const initialize = async () => {
      try {
        await initLIFF();
        const userProfile = await getLiffProfile();
        const { userId, tab } = getWebParams();
        const finalUserId = userId || userProfile?.userId || 'test-user';
        
        setProfile({ 
          ...userProfile, 
          userId: finalUserId,
          displayName: userProfile?.displayName || '用戶'
        });

        // 根據 URL 參數設定初始 Tab
        if (tab && ['bookmarks', 'folders', 'profile'].includes(tab)) {
          setActiveTab(tab);
        }
      } catch (error) {
        console.error('初始化失敗:', error);
        setProfile({ userId: 'test-user', displayName: '用戶' });
      } finally {
        setLoading(false);
      }
    };

    initialize();
  }, []);

  // 更新 URL 參數
  const updateURL = (tab) => {
    const url = new URL(window.location);
    url.searchParams.set('tab', tab);
    if (profile?.userId) {
      url.searchParams.set('userId', profile.userId);
    }
    window.history.replaceState({}, '', url);
  };

  // 切換 Tab
  const handleTabChange = (tab) => {
    setActiveTab(tab);
    updateURL(tab);
    setSidebarOpen(false); // 關閉側邊欄（手機版）
  };

  // 返回處理
  const handleBack = () => {
    if (window.history.length > 1) {
      window.history.back();
    } else {
      window.close();
    }
  };

  // Tab 配置
  const tabs = [
    {
      id: 'bookmarks',
      name: '書籤總覽',
      icon: BookOpen,
      component: BookmarkHistory
    },
    {
      id: 'folders',
      name: '資料夾',
      icon: Folder,
      component: FoldersContent
    },
    {
      id: 'profile',
      name: '個人設定',
      icon: User,
      component: ProfileContent
    }
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">載入中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* 側邊欄背景遮罩 (手機版) */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* 側邊欄 */}
      <div className={`
        fixed lg:static inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {/* 側邊欄頭部 */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <BookOpen className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-gray-900">BriefCard</h1>
              <p className="text-xs text-gray-500">智能書籤管理</p>
            </div>
          </div>
          <button 
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-1 text-gray-400 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* 用戶資訊 */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
              <User className="h-5 w-5 text-gray-600" />
            </div>
            <div>
              <p className="font-medium text-gray-900">{profile?.displayName}</p>
              <p className="text-xs text-gray-500">ID: {profile?.userId}</p>
            </div>
          </div>
        </div>

        {/* 導航選單 */}
        <nav className="p-4 space-y-2">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            
            return (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={`
                  w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors
                  ${isActive 
                    ? 'bg-blue-50 text-blue-700 border border-blue-200' 
                    : 'text-gray-700 hover:bg-gray-50'
                  }
                `}
              >
                <Icon className={`h-5 w-5 ${isActive ? 'text-blue-600' : 'text-gray-400'}`} />
                <span className="font-medium">{tab.name}</span>
              </button>
            );
          })}
        </nav>

        {/* 底部操作 */}
        <div className="absolute bottom-4 left-4 right-4">
          <button
            onClick={handleBack}
            className="w-full flex items-center gap-2 px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>返回 LINE</span>
          </button>
        </div>
      </div>

      {/* 主要內容區域 */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* 頂部導航欄 (手機版) */}
        <div className="lg:hidden bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between sticky top-0 z-30">
          <button 
            onClick={() => setSidebarOpen(true)}
            className="p-2 text-gray-600 hover:text-gray-900"
          >
            <Menu className="h-5 w-5" />
          </button>
          <h1 className="font-semibold text-gray-900">
            {tabs.find(tab => tab.id === activeTab)?.name}
          </h1>
          <div className="w-9" /> {/* 佔位符保持居中 */}
        </div>

        {/* Tab 導航 (桌面版) */}
        <div className="hidden lg:block bg-white border-b border-gray-200 sticky top-0 z-30">
          <div className="px-6 py-4">
            <div className="flex space-x-8">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                
                return (
                  <button
                    key={tab.id}
                    onClick={() => handleTabChange(tab.id)}
                    className={`
                      flex items-center gap-2 px-1 py-2 border-b-2 font-medium text-sm transition-colors
                      ${isActive 
                        ? 'border-blue-500 text-blue-600' 
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }
                    `}
                  >
                    <Icon className="h-4 w-4" />
                    {tab.name}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* 內容區域 */}
        <div className="flex-1 overflow-auto">
          {ActiveComponent && (
            <div className="h-full">
              {activeTab === 'bookmarks' && (
                <div className="p-6">
                  <ActiveComponent userId={profile?.userId} />
                </div>
              )}
              {activeTab === 'folders' && (
                <ActiveComponent />
              )}
              {activeTab === 'profile' && (
                <ActiveComponent />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;