// 網頁版配置（不再使用 LIFF）
export const APP_CONFIG = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'https://your-app.zeabur.app',
};

// 模擬初始化（保持介面一致）
export const initLIFF = async () => {
  // 網頁版不需要 LIFF 初始化
  return true;
};

// 模擬用戶資料（從 URL 參數獲取）
export const getLiffProfile = async () => {
  const params = getWebParams();
  return {
    userId: params.userId,
    displayName: '用戶', // 預設顯示名稱
  };
};

// 關閉視窗或返回上一頁
export const closeLIFF = () => {
  if (window.history.length > 1) {
    window.history.back();
  } else {
    window.close();
  }
};

// 獲取 URL 參數（重命名為更通用的名稱）
export const getWebParams = () => {
  const urlParams = new URLSearchParams(window.location.search);
  return {
    bookmarkId: urlParams.get('bookmarkId'),
    userId: urlParams.get('userId'),
  };
};

// 為了向後兼容，保留原函數名
export const getLiffParams = getWebParams;