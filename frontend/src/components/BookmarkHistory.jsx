import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Search, 
  Calendar, 
  BookOpen, 
  ChevronLeft,
  ChevronRight,
  Clock,
  Loader2,
  Edit3,
  ExternalLink
} from 'lucide-react';
import { APP_CONFIG } from '../liff';

const BookmarkHistory = ({ userId }) => {
  // 狀態管理
  const [bookmarks, setBookmarks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  
  // 分頁狀態
  const [currentPage, setCurrentPage] = useState(1);
  const [pagination, setPagination] = useState({});
  
  // 載入書籤歷史
  const loadBookmarkHistory = async (page = 1) => {
    try {
      setLoading(true);
      const response = await axios.get(
        `${APP_CONFIG.API_BASE_URL}/api/v1/bookmarks/history`,
        {
          params: {
            user_id: userId,
            page: page,
            limit: 20
          }
        }
      );
      
      setBookmarks(response.data.bookmarks);
      setPagination(response.data.pagination);
      setCurrentPage(page);
    } catch (error) {
      console.error('載入書籤歷史失敗:', error);
    } finally {
      setLoading(false);
    }
  };

  // 按日期分組書籤
  const groupBookmarksByDate = (bookmarks) => {
    const groups = {};
    bookmarks.forEach(bookmark => {
      const date = new Date(bookmark.created_at).toLocaleDateString('zh-TW', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'long'
      });
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(bookmark);
    });
    return groups;
  };

  // 搜索書籤
  const handleSearch = async (query) => {
    if (!query || query.length < 2) {
      setSearchResults([]);
      return;
    }
    
    try {
      setSearching(true);
      const response = await axios.get(
        `${APP_CONFIG.API_BASE_URL}/api/v1/bookmarks/search`,
        {
          params: {
            user_id: userId,
            q: query,
            limit: 50
          }
        }
      );
      
      setSearchResults(response.data.results);
    } catch (error) {
      console.error('搜索失敗:', error);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  // 處理搜索輸入
  const handleSearchInput = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    
    // 防抖搜索
    clearTimeout(window.searchTimeout);
    window.searchTimeout = setTimeout(() => {
      handleSearch(query);
    }, 500);
  };

  // 格式化日期
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-TW', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // 截斷文本
  const truncateText = (text, maxLength = 100) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  // 書籤預覽卡片組件 - 簡化版本，點擊進入編輯頁
  const BookmarkPreviewCard = ({ bookmark, onClick }) => (
    <div 
      onClick={() => onClick(bookmark)}
      className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-all cursor-pointer hover:border-blue-300 p-3"
    >
      <div className="flex gap-3">
        {/* 預覽圖片 */}
        {bookmark.image_url && (
          <div className="flex-shrink-0">
            <img 
              src={bookmark.image_url} 
              alt={bookmark.title}
              className="w-16 h-16 object-cover rounded-md"
              onError={(e) => {e.target.style.display = 'none'}}
            />
          </div>
        )}
        
        {/* 內容預覽 */}
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-gray-900 mb-1 line-clamp-2">
            {bookmark.title || bookmark.url}
          </h3>
          
          {bookmark.description && (
            <p className="text-sm text-gray-600 mb-2 line-clamp-2">
              {bookmark.description}
            </p>
          )}
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Clock className="h-3 w-3" />
              <span>{new Date(bookmark.created_at).toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
            
            <div className="flex items-center gap-1">
              <Edit3 className="h-3 w-3 text-blue-500" />
              <ExternalLink className="h-3 w-3 text-gray-400" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // 處理卡片點擊 - 導向編輯頁面
  const handleCardClick = (bookmark) => {
    // 構建編輯頁面 URL
    const editUrl = `https://vibe-test-brief-card.vercel.app?bookmarkId=${bookmark.id}&userId=${userId}`;
    window.open(editUrl, '_blank');
  };

  // 初始化載入
  useEffect(() => {
    if (userId) {
      loadBookmarkHistory();
    }
  }, [userId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">載入中...</span>
      </div>
    );
  }

  // 顯示的書籤列表和日期分組
  const displayBookmarks = searchQuery ? searchResults : bookmarks;
  const groupedBookmarks = groupBookmarksByDate(displayBookmarks);

  return (
    <div className="max-w-4xl mx-auto p-4 space-y-6">
      {/* 標題 */}
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">我的書籤</h1>
        <p className="text-gray-600">瀏覽您收藏的精彩內容</p>
      </div>

      {/* 搜索框 */}
      <div className="relative max-w-md mx-auto">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="搜索書籤..."
          value={searchQuery}
          onChange={handleSearchInput}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        {searching && (
          <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 animate-spin text-blue-600" />
        )}
      </div>

      {/* 搜索結果提示 */}
      {searchQuery && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-blue-800">
            搜索 "{searchQuery}" 找到 {searchResults.length} 個結果
          </p>
          {searchResults.length === 0 && (
            <p className="text-blue-600 text-sm mt-1">
              嘗試使用不同的關鍵字或檢查拼寫
            </p>
          )}
        </div>
      )}

      {/* 按日期分組的書籤列表 */}
      {Object.keys(groupedBookmarks).length > 0 ? (
        <div className="space-y-6">
          {Object.entries(groupedBookmarks)
            .sort(([dateA], [dateB]) => new Date(dateB) - new Date(dateA))
            .map(([date, dateBookmarks]) => (
            <div key={date} className="space-y-3">
              {/* 日期標題容器 */}
              <div className="flex items-center gap-3">
                <Calendar className="h-5 w-5 text-blue-600" />
                <h2 className="text-lg font-semibold text-gray-900">{date}</h2>
                <div className="flex-1 h-px bg-gray-200"></div>
                <span className="text-sm text-gray-500">{dateBookmarks.length} 個書籤</span>
              </div>
              
              {/* 該日期的書籤卡片 */}
              <div className="space-y-3 pl-8">
                {dateBookmarks.map((bookmark) => (
                  <BookmarkPreviewCard 
                    key={bookmark.id} 
                    bookmark={bookmark}
                    onClick={handleCardClick}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {searchQuery ? '沒有找到相關書籤' : '還沒有書籤'}
          </h3>
          <p className="text-gray-600">
            {searchQuery ? '嘗試使用不同的搜索關鍵字' : '開始收藏您喜歡的網頁內容吧！'}
          </p>
        </div>
      )}

      {/* 分頁控制 */}
      {!searchQuery && pagination.total_pages > 1 && (
        <div className="flex items-center justify-center gap-4">
          <button
            onClick={() => loadBookmarkHistory(currentPage - 1)}
            disabled={!pagination.has_prev}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="h-4 w-4" />
            上一頁
          </button>
          
          <span className="text-sm text-gray-700">
            第 {pagination.current_page} 頁，共 {pagination.total_pages} 頁
          </span>
          
          <button
            onClick={() => loadBookmarkHistory(currentPage + 1)}
            disabled={!pagination.has_next}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            下一頁
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
};

export default BookmarkHistory;