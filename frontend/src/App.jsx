import React, { useState, useEffect } from 'react';
import EditCard from './EditCard';
import BookmarkHistoryPage from './BookmarkHistoryPage';
import FoldersPage from './FoldersPage';
import ProfilePage from './ProfilePage';
import { getWebParams, isLiffEnvironment } from './liff';
import './index.css';

function App() {
  const [currentTab, setCurrentTab] = useState('edit');
  const [params, setParams] = useState({});

  useEffect(() => {
    // 獲取 URL 參數
    const urlParams = getWebParams();
    setParams(urlParams);

    // 根據 tab 參數決定顯示哪個頁面
    const tab = new URLSearchParams(window.location.search).get('tab');
    if (tab) {
      setCurrentTab(tab);
    } else if (urlParams.bookmarkId) {
      // 如果有 bookmarkId，顯示編輯頁面
      setCurrentTab('edit');
    } else {
      // 預設顯示書籤列表
      setCurrentTab('bookmarks');
    }
  }, []);

  // 渲染對應的頁面組件
  const renderPage = () => {
    switch (currentTab) {
      case 'bookmarks':
        return <BookmarkHistoryPage userId={params.userId} />;
      case 'folders':
        return <FoldersPage userId={params.userId} />;
      case 'profile':
        return <ProfilePage userId={params.userId} />;
      case 'edit':
      default:
        return <EditCard />;
    }
  };

  return (
    <div className="App">
      {/* 如果在 LIFF 環境中，添加狀態提示 */}
      {isLiffEnvironment() && (
        <div className="bg-blue-50 text-blue-700 text-xs px-3 py-1 text-center border-b">
          ✨ LINE 內建應用模式
        </div>
      )}
      
      {renderPage()}
    </div>
  );
}

export default App;