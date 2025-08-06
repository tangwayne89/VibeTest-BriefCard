import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Search, 
  Calendar, 
  BookOpen, 
  TrendingUp,
  Filter,
  Grid,
  List,
  ChevronLeft,
  ChevronRight,
  BarChart3,
  Clock,
  Loader2
} from 'lucide-react';
import { APP_CONFIG } from '../liff';

const BookmarkHistory = ({ userId }) => {
  // 狀態管理
  const [bookmarks, setBookmarks] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [viewMode, setViewMode] = useState('list'); // 'list' or 'grid'
  
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

  // 載入統計資訊
  const loadStats = async () => {
    try {
      const response = await axios.get(
        `${APP_CONFIG.API_BASE_URL}/api/v1/bookmarks/stats`,
        {
          params: { user_id: userId }
        }
      );
      
      setStats(response.data);
    } catch (error) {
      console.error('載入統計資訊失敗:', error);
    }
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

  // 書籤卡片組件
  const BookmarkCard = ({ bookmark, isGrid = false }) => (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow ${isGrid ? 'p-4' : 'p-4 flex gap-4'}`}>
      {/* 圖片 */}
      {bookmark.image_url && (
        <div className={isGrid ? 'mb-3' : 'flex-shrink-0'}>
          <img 
            src={bookmark.image_url} 
            alt={bookmark.title}
            className={isGrid ? 'w-full h-32 object-cover rounded-md' : 'w-16 h-16 object-cover rounded-md'}
            onError={(e) => {e.target.style.display = 'none'}}
          />
        </div>
      )}
      
      {/* 內容 */}
      <div className="flex-1 min-w-0">
        <h3 className="font-medium text-gray-900 mb-1">
          {truncateText(bookmark.title || bookmark.url, isGrid ? 60 : 80)}
        </h3>
        
        {bookmark.description && (
          <p className="text-sm text-gray-600 mb-2">
            {truncateText(bookmark.description, isGrid ? 80 : 120)}
          </p>
        )}
        
        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center gap-2">
            <Clock className="h-3 w-3" />
            <span>{formatDate(bookmark.created_at)}</span>
          </div>
          
          {bookmark.folder_id && (
            <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded-full text-xs">
              已分類
            </span>
          )}
        </div>
        
        {bookmark.notes && (
          <div className="mt-2 p-2 bg-gray-50 rounded text-sm text-gray-600">
            {truncateText(bookmark.notes, 100)}
          </div>
        )}
      </div>
    </div>
  );

  // 統計卡片組件
  const StatCard = ({ title, value, icon: Icon, color = "blue" }) => (
    <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className={`text-2xl font-bold text-${color}-600`}>{value}</p>
        </div>
        <Icon className={`h-8 w-8 text-${color}-500`} />
      </div>
    </div>
  );

  // 初始化載入
  useEffect(() => {
    if (userId) {
      loadBookmarkHistory();
      loadStats();
    }
  }, [userId]);

  // 顯示的書籤列表
  const displayBookmarks = searchQuery ? searchResults : bookmarks;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">載入中...</span>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-6">
      {/* 標題 */}
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">我的書籤歷史</h1>
        <p className="text-gray-600">管理和查看您收藏的所有書籤</p>
      </div>

      {/* 統計卡片 */}
      {stats.statistics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard 
            title="總書籤" 
            value={stats.statistics.total} 
            icon={BookOpen}
            color="blue"
          />
          <StatCard 
            title="今日新增" 
            value={stats.statistics.today} 
            icon={TrendingUp}
            color="green"
          />
          <StatCard 
            title="本週新增" 
            value={stats.statistics.this_week} 
            icon={Calendar}
            color="purple"
          />
          <StatCard 
            title="本月新增" 
            value={stats.statistics.this_month} 
            icon={BarChart3}
            color="orange"
          />
        </div>
      )}

      {/* 搜索和視圖控制 */}
      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
        {/* 搜索框 */}
        <div className="relative flex-1 max-w-md">
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

        {/* 視圖切換 */}
        <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded-md transition-colors ${
              viewMode === 'list' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <List className="h-4 w-4" />
          </button>
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded-md transition-colors ${
              viewMode === 'grid' ? 'bg-white shadow-sm text-blue-600' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Grid className="h-4 w-4" />
          </button>
        </div>
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

      {/* 書籤列表 */}
      {displayBookmarks.length > 0 ? (
        <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4' : 'space-y-4'}>
          {displayBookmarks.map((bookmark) => (
            <BookmarkCard 
              key={bookmark.id} 
              bookmark={bookmark} 
              isGrid={viewMode === 'grid'}
            />
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