// LIFF 配置
export const LIFF_ID = '2007890677-Wa6jeBz3';
export const LIFF_URL = 'https://liff.line.me/2007890677-Wa6jeBz3';

export const APP_CONFIG = {
  API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'https://briefcard.zeabur.app',
  LIFF_ID,
  LIFF_URL,
};

// 檢查是否在 LIFF 環境中
export const isLiffEnvironment = () => {
  return typeof window !== 'undefined' && 
         (window.location.href.includes('liff.line.me') || 
          window.location.href.includes('line.me') ||
          window.liff);
};

// 動態載入 LIFF SDK
const loadLiffSDK = () => {
  return new Promise((resolve, reject) => {
    if (window.liff) {
      resolve(window.liff);
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://static.line-scdn.net/liff/edge/2/sdk.js';
    script.onload = () => {
      if (window.liff) {
        resolve(window.liff);
      } else {
        reject(new Error('LIFF SDK 載入失敗'));
      }
    };
    script.onerror = () => reject(new Error('無法載入 LIFF SDK'));
    document.head.appendChild(script);
  });
};

// 初始化 LIFF
export const initLIFF = async () => {
  try {
    // 如果不在 LIFF 環境中，返回 true（網頁版模式）
    if (!isLiffEnvironment()) {
      console.log('🌐 運行在網頁版模式');
      return true;
    }

    // 載入 LIFF SDK
    const liff = await loadLiffSDK();
    
    // 初始化 LIFF
    await liff.init({ liffId: LIFF_ID });
    
    // 檢查登入狀態
    if (!liff.isLoggedIn()) {
      console.log('👤 用戶未登入，跳轉到登入頁面');
      liff.login();
      return false;
    }
    
    console.log('✅ LIFF 初始化成功');
    return true;
    
  } catch (error) {
    console.error('❌ LIFF 初始化失敗:', error);
    // 如果 LIFF 初始化失敗，回退到網頁版模式
    return true;
  }
};

// 獲取用戶資料
export const getLiffProfile = async () => {
  try {
    // 如果在 LIFF 環境中
    if (isLiffEnvironment() && window.liff && window.liff.isLoggedIn()) {
      const profile = await window.liff.getProfile();
      return {
        userId: profile.userId,
        displayName: profile.displayName,
        pictureUrl: profile.pictureUrl,
        statusMessage: profile.statusMessage,
      };
    }
    
    // 網頁版模式：從 URL 參數獲取
    const params = getWebParams();
    return {
      userId: params.userId || 'web_user_' + Date.now(),
      displayName: params.displayName || '網頁用戶',
      pictureUrl: null,
      statusMessage: null,
    };
    
  } catch (error) {
    console.error('❌ 獲取用戶資料失敗:', error);
    // 回退到預設用戶
    return {
      userId: 'fallback_user_' + Date.now(),
      displayName: '用戶',
      pictureUrl: null,
      statusMessage: null,
    };
  }
};

// 關閉視窗或返回上一頁
export const closeLIFF = () => {
  try {
    // 如果在 LIFF 環境中，使用 LIFF 的關閉方法
    if (isLiffEnvironment() && window.liff) {
      window.liff.closeWindow();
      return;
    }
    
    // 網頁版模式
    if (window.history.length > 1) {
      window.history.back();
    } else {
      window.close();
    }
  } catch (error) {
    console.error('❌ 關閉視窗失敗:', error);
    // 回退方法
    window.history.back();
  }
};

// 分享功能
export const shareContent = async (content) => {
  try {
    // 如果在 LIFF 環境中，使用 LIFF 分享
    if (isLiffEnvironment() && window.liff) {
      await window.liff.shareTargetPicker([
        {
          type: 'flex',
          altText: content.altText || '分享書籤卡片',
          contents: content.flexMessage || createDefaultFlexMessage(content)
        }
      ]);
      return true;
    }
    
    // 網頁版模式：使用 Web Share API 或回退方法
    if (navigator.share) {
      await navigator.share({
        title: content.title,
        text: content.description,
        url: content.url || window.location.href
      });
      return true;
    } else {
      // 回退：複製到剪貼板
      await navigator.clipboard.writeText(content.url || window.location.href);
      alert('連結已複製到剪貼板！');
      return true;
    }
    
  } catch (error) {
    console.error('❌ 分享失敗:', error);
    return false;
  }
};

// 創建預設的 Flex Message
const createDefaultFlexMessage = (content) => {
  return {
    type: "bubble",
    hero: content.imageUrl ? {
      type: "image",
      url: content.imageUrl,
      size: "full",
      aspectRatio: "20:13",
      aspectMode: "cover"
    } : undefined,
    body: {
      type: "box",
      layout: "vertical",
      contents: [
        {
          type: "text",
          text: content.title || "書籤卡片",
          weight: "bold",
          size: "xl",
          wrap: true
        },
        {
          type: "text",
          text: content.description || "來看看這個有趣的內容！",
          size: "sm",
          color: "#666666",
          wrap: true,
          margin: "md"
        }
      ]
    },
    footer: {
      type: "box",
      layout: "vertical",
      spacing: "sm",
      contents: [
        {
          type: "button",
          style: "primary",
          height: "sm",
          action: {
            type: "uri",
            label: "查看詳情",
            uri: content.url || LIFF_URL
          }
        }
      ]
    }
  };
};

// 發送訊息到聊天室
export const sendMessage = async (message) => {
  try {
    if (isLiffEnvironment() && window.liff) {
      await window.liff.sendMessages([{
        type: 'text',
        text: message
      }]);
      return true;
    }
    
    console.log('網頁版模式：無法發送訊息到 LINE');
    return false;
    
  } catch (error) {
    console.error('❌ 發送訊息失敗:', error);
    return false;
  }
};

// 獲取 LIFF 環境資訊
export const getLiffContext = () => {
  try {
    if (isLiffEnvironment() && window.liff) {
      return {
        type: window.liff.getContext()?.type || 'unknown',
        viewType: window.liff.getContext()?.viewType || 'unknown',
        userId: window.liff.getContext()?.userId,
        utouId: window.liff.getContext()?.utouId,
        roomId: window.liff.getContext()?.roomId,
        groupId: window.liff.getContext()?.groupId
      };
    }
    
    return {
      type: 'web',
      viewType: 'full',
      userId: null,
      utouId: null,
      roomId: null,
      groupId: null
    };
    
  } catch (error) {
    console.error('❌ 獲取 LIFF 環境資訊失敗:', error);
    return null;
  }
};

// 獲取 URL 參數（重命名為更通用的名稱）
export const getWebParams = () => {
  const urlParams = new URLSearchParams(window.location.search);
  return {
    bookmarkId: urlParams.get('bookmarkId'),
    userId: urlParams.get('userId'),
    displayName: urlParams.get('displayName'),
  };
};

// 為了向後兼容，保留原函數名
export const getLiffParams = getWebParams;

// 檢查是否為行動裝置
export const isMobileDevice = () => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
};

// 獲取裝置資訊
export const getDeviceInfo = () => {
  return {
    isMobile: isMobileDevice(),
    isLiff: isLiffEnvironment(),
    userAgent: navigator.userAgent,
    language: navigator.language,
    platform: navigator.platform
  };
};