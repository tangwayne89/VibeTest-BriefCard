import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Save, 
  Share2, 
  Folder, 
  Edit3, 
  Image, 
  ArrowLeft,
  Loader2,
  Sparkles
} from 'lucide-react';
import { initLIFF, getLiffProfile, closeLIFF, getLiffParams, APP_CONFIG } from './liff';

const EditCard = () => {
  // 狀態管理
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [profile, setProfile] = useState(null);
  const [bookmark, setBookmark] = useState(null);
  const [folders, setFolders] = useState([]);
  
  // 表單狀態
  const [formData, setFormData] = useState({
    title: '',
    folder_id: '',
    notes: '',
    url: '',
    image_url: ''
  });

  // 錯誤狀態
  const [error, setError] = useState(null);

  // 初始化
  useEffect(() => {
    const initialize = async () => {
      try {
        // 初始化 LIFF
        const liffReady = await initLIFF();
        if (!liffReady) return;

        // 獲取用戶資料
        const userProfile = await getLiffProfile();
        setProfile(userProfile);

        // 獲取 URL 參數
        const { bookmarkId, userId } = getLiffParams();
        
        if (!bookmarkId) {
          setError('缺少書籤 ID');
          return;
        }

        // 並行獲取書籤資料和資料夾列表
        await Promise.all([
          loadBookmark(bookmarkId),
          loadFolders(userId || userProfile?.userId)
        ]);

      } catch (err) {
        console.error('初始化失敗:', err);
        setError('載入失敗，請重試');
      } finally {
        setIsLoading(false);
      }
    };

    initialize();
  }, []);

  // 載入書籤資料
  const loadBookmark = async (bookmarkId) => {
    try {
      const response = await axios.get(
        `${APP_CONFIG.API_BASE_URL}/api/bookmarks/${bookmarkId}`
      );
      
      const bookmarkData = response.data;
      setBookmark(bookmarkData);
      
      // 更新表單資料
      setFormData({
        title: bookmarkData.title || '',
        folder_id: bookmarkData.folder_id || '',
        notes: bookmarkData.notes || '',
        url: bookmarkData.url || '',
        image_url: bookmarkData.image_url || ''
      });
    } catch (err) {
      console.error('載入書籤失敗:', err);
      setError('載入書籤資料失敗');
    }
  };

  // 載入資料夾列表
  const loadFolders = async (userId) => {
    try {
      const response = await axios.get(
        `${APP_CONFIG.API_BASE_URL}/api/folders?user_id=${userId}`
      );
      setFolders(response.data.folders || []);
    } catch (err) {
      console.error('載入資料夾失敗:', err);
      // 資料夾載入失敗不是致命錯誤，可以繼續
    }
  };

  // 處理表單變更
  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  // 儲存變更
  const handleSave = async () => {
    if (!bookmark) return;
    
    setIsSaving(true);
    try {
      await axios.patch(
        `${APP_CONFIG.API_BASE_URL}/api/bookmarks/${bookmark.id}`,
        {
          title: formData.title,
          folder_id: formData.folder_id || null,
          notes: formData.notes
        }
      );

      // 顯示成功訊息（可以使用 toast 或其他 UI 元件）
      alert('✅ 儲存成功！');
      
      // 關閉 LIFF 視窗
      setTimeout(() => {
        closeLIFF();
      }, 1000);
      
    } catch (err) {
      console.error('儲存失敗:', err);
      alert('❌ 儲存失敗，請重試');
    } finally {
      setIsSaving(false);
    }
  };

  // 分享功能 (Phase 2)
  const handleShare = () => {
    alert('🚀 分享功能即將推出！');
  };

  // 產生 AI 摘要 (Phase 2)
  const handleGenerateAISummary = () => {
    alert('🤖 AI 摘要功能即將推出！');
  };

  // 載入中狀態
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-line-green mx-auto mb-4" />
          <p className="text-gray-600">載入中...</p>
        </div>
      </div>
    );
  }

  // 錯誤狀態
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center p-6">
          <div className="text-red-500 text-xl mb-4">❌</div>
          <p className="text-gray-800 mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="btn-primary"
          >
            重新載入
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 頂部導航 */}
      <header className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <button 
            onClick={closeLIFF}
            className="flex items-center text-gray-600 hover:text-gray-800"
          >
            <ArrowLeft className="h-5 w-5 mr-1" />
            返回
          </button>
          <h1 className="text-lg font-semibold text-gray-800">編輯卡片</h1>
          <div className="w-12"></div> {/* 佔位符 */}
        </div>
      </header>

      {/* 主要內容 */}
      <main className="p-4 pb-20">
        {/* 預覽圖片 */}
        <div className="card mb-6">
          <div className="flex items-center mb-3">
            <Image className="h-5 w-5 text-gray-600 mr-2" />
            <h2 className="text-lg font-medium text-gray-800">預覽圖片</h2>
          </div>
          
          <div className="aspect-video bg-gray-100 rounded-lg overflow-hidden">
            {formData.image_url ? (
              <img 
                src={formData.image_url} 
                alt="預覽"
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.target.src = '/icon.png'; // 回退到預設圖片
                }}
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-400">
                <Image className="h-12 w-12" />
              </div>
            )}
          </div>
        </div>

        {/* 標題編輯 */}
        <div className="card mb-6">
          <div className="flex items-center mb-3">
            <Edit3 className="h-5 w-5 text-gray-600 mr-2" />
            <h2 className="text-lg font-medium text-gray-800">標題</h2>
          </div>
          
          <input
            type="text"
            value={formData.title}
            onChange={(e) => handleInputChange('title', e.target.value)}
            placeholder="輸入標題..."
            className="input-field"
          />
        </div>

        {/* 資料夾選擇 */}
        <div className="card mb-6">
          <div className="flex items-center mb-3">
            <Folder className="h-5 w-5 text-gray-600 mr-2" />
            <h2 className="text-lg font-medium text-gray-800">資料夾</h2>
          </div>
          
          <select
            value={formData.folder_id}
            onChange={(e) => handleInputChange('folder_id', e.target.value)}
            className="input-field"
          >
            <option value="">選擇資料夾...</option>
            {folders.map(folder => (
              <option key={folder.id} value={folder.id}>
                {folder.name}
              </option>
            ))}
          </select>
        </div>

        {/* 筆記 */}
        <div className="card mb-6">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center">
              <Edit3 className="h-5 w-5 text-gray-600 mr-2" />
              <h2 className="text-lg font-medium text-gray-800">筆記</h2>
            </div>
            <button 
              onClick={handleGenerateAISummary}
              className="flex items-center text-sm text-line-green hover:text-line-green-dark"
            >
              <Sparkles className="h-4 w-4 mr-1" />
              AI 摘要
            </button>
          </div>
          
          <textarea
            value={formData.notes}
            onChange={(e) => handleInputChange('notes', e.target.value)}
            placeholder="新增你的筆記..."
            rows={6}
            className="input-field resize-none"
          />
        </div>

        {/* 原始連結資訊 */}
        <div className="card mb-6">
          <h3 className="text-sm font-medium text-gray-600 mb-2">原始連結</h3>
          <a 
            href={formData.url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-line-green hover:text-line-green-dark text-sm break-all"
          >
            {formData.url}
          </a>
        </div>
      </main>

      {/* 底部操作按鈕 */}
      <footer className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4">
        <div className="flex gap-3">
          <button 
            onClick={handleShare}
            className="btn-secondary flex items-center justify-center flex-1"
          >
            <Share2 className="h-4 w-4 mr-2" />
            分享
          </button>
          
          <button 
            onClick={handleSave}
            disabled={isSaving}
            className="btn-primary flex items-center justify-center flex-1"
          >
            {isSaving ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Save className="h-4 w-4 mr-2" />
            )}
            {isSaving ? '儲存中...' : '儲存變更'}
          </button>
        </div>
      </footer>
    </div>
  );
};

export default EditCard;