import React, { useState, useEffect } from 'react';
import BookmarkHistory from './components/BookmarkHistory';
import { initLIFF, getLiffProfile } from './liff';
import { ArrowLeft } from 'lucide-react';

const BookmarkHistoryPage = () => {
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initialize = async () => {
      try {
        await initLIFF();
        const userProfile = await getLiffProfile();
        setProfile(userProfile);
      } catch (error) {
        console.error('初始化失敗:', error);
        // 如果不在 LINE 環境中，使用測試用戶 ID
        setProfile({ userId: 'test-user' });
      } finally {
        setIsLoading(false);
      }
    };

    initialize();
  }, []);

  const handleBack = () => {
    if (window.history.length > 1) {
      window.history.back();
    } else {
      window.close();
    }
  };

  if (isLoading) {
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
    <div className="min-h-screen bg-gray-50">
      {/* 頂部導航 */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center">
          <button 
            onClick={handleBack}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
            <span>返回</span>
          </button>
        </div>
      </div>

      {/* 主要內容 */}
      <div className="py-6">
        <BookmarkHistory userId={profile?.userId} />
      </div>
    </div>
  );
};

export default BookmarkHistoryPage;