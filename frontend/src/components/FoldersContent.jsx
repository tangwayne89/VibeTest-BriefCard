import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Plus, 
  Folder, 
  Edit3, 
  Trash2, 
  BookOpen,
  Loader2,
  Search
} from 'lucide-react';
import { initLIFF, getLiffProfile, getWebParams, APP_CONFIG } from '../liff';

const FoldersContent = () => {
  const [profile, setProfile] = useState(null);
  const [folders, setFolders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [editingFolder, setEditingFolder] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  // 表單狀態
  const [formData, setFormData] = useState({
    name: '',
    color: '#1976D2',
    is_default: false
  });

  // 顏色選項
  const colorOptions = [
    '#1976D2', '#2E7D32', '#F57C00', '#D32F2F',
    '#7B1FA2', '#0288D1', '#388E3C', '#F9A825',
    '#C2185B', '#5D4037', '#616161', '#455A64'
  ];

  // 初始化
  useEffect(() => {
    const initialize = async () => {
      try {
        await initLIFF();
        const userProfile = await getLiffProfile();
        const { userId } = getWebParams();
        const finalUserId = userId || userProfile?.userId || 'test-user';
        
        setProfile({ ...userProfile, userId: finalUserId });
        await loadFolders(finalUserId);
      } catch (error) {
        console.error('初始化失敗:', error);
        setProfile({ userId: 'test-user' });
        await loadFolders('test-user');
      } finally {
        setLoading(false);
      }
    };

    initialize();
  }, []);

  // 載入資料夾
  const loadFolders = async (userId) => {
    try {
      const response = await axios.get(
        `${APP_CONFIG.API_BASE_URL}/api/folders?user_id=${userId}`
      );
      setFolders(response.data.folders || []);
    } catch (error) {
      console.error('載入資料夾失敗:', error);
      setFolders([]);
    }
  };

  // 創建資料夾
  const handleCreateFolder = async () => {
    if (!formData.name.trim()) return;
    
    setIsCreating(true);
    try {
      const response = await axios.post(
        `${APP_CONFIG.API_BASE_URL}/api/folders`,
        {
          user_id: profile.userId,
          name: formData.name.trim(),
          color: formData.color,
          is_default: formData.is_default,
          sort_order: folders.length
        }
      );
      
      setFolders(prev => [...prev, response.data]);
      setFormData({ name: '', color: '#1976D2', is_default: false });
      setShowCreateForm(false);
      
    } catch (error) {
      console.error('創建資料夾失敗:', error);
      alert('❌ 創建資料夾失敗，請重試');
    } finally {
      setIsCreating(false);
    }
  };

  // 更新資料夾
  const handleUpdateFolder = async () => {
    if (!editingFolder || !formData.name.trim()) return;
    
    setIsCreating(true);
    try {
      const response = await axios.put(
        `${APP_CONFIG.API_BASE_URL}/api/folders/${editingFolder.id}`,
        {
          name: formData.name.trim(),
          color: formData.color,
          is_default: formData.is_default
        }
      );
      
      setFolders(prev => prev.map(folder => 
        folder.id === editingFolder.id ? response.data : folder
      ));
      
      setEditingFolder(null);
      setFormData({ name: '', color: '#1976D2', is_default: false });
      setShowCreateForm(false);
      
    } catch (error) {
      console.error('更新資料夾失敗:', error);
      alert('❌ 更新資料夾失敗，請重試');
    } finally {
      setIsCreating(false);
    }
  };

  // 刪除資料夾
  const handleDeleteFolder = async (folderId) => {
    if (!confirm('確定要刪除這個資料夾嗎？資料夾內的書籤將移至未分類。')) return;
    
    try {
      await axios.delete(`${APP_CONFIG.API_BASE_URL}/api/folders/${folderId}`);
      setFolders(prev => prev.filter(folder => folder.id !== folderId));
    } catch (error) {
      console.error('刪除資料夾失敗:', error);
      alert('❌ 刪除資料夾失敗，請重試');
    }
  };

  // 開始編輯
  const startEdit = (folder) => {
    setEditingFolder(folder);
    setFormData({
      name: folder.name,
      color: folder.color,
      is_default: folder.is_default
    });
    setShowCreateForm(true);
  };

  // 取消編輯
  const cancelEdit = () => {
    setEditingFolder(null);
    setFormData({ name: '', color: '#1976D2', is_default: false });
    setShowCreateForm(false);
  };

  // 過濾資料夾
  const filteredFolders = folders.filter(folder =>
    folder.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
    <div className="max-w-6xl mx-auto p-6">
      {/* 頁面標題和操作 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Folder className="h-6 w-6 text-blue-600" />
          <h1 className="text-2xl font-bold text-gray-900">資料夾管理</h1>
        </div>
        
        <button
          onClick={() => setShowCreateForm(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          <span>新增資料夾</span>
        </button>
      </div>

      {/* 搜尋框 */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜尋資料夾..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* 資料夾網格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {filteredFolders.map(folder => (
          <div
            key={folder.id}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <div 
                  className="w-10 h-10 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: folder.color }}
                >
                  <Folder className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">{folder.name}</h3>
                  {folder.is_default && (
                    <span className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded-full">預設</span>
                  )}
                </div>
              </div>
              
              <div className="flex items-center gap-1">
                <button
                  onClick={() => startEdit(folder)}
                  className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                >
                  <Edit3 className="h-4 w-4" />
                </button>
                {!folder.is_default && (
                  <button
                    onClick={() => handleDeleteFolder(folder.id)}
                    className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>
            
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <div className="flex items-center gap-1">
                <BookOpen className="h-4 w-4" />
                <span>0 個書籤</span>
              </div>
              <div className="text-xs">
                {new Date(folder.created_at).toLocaleDateString()}
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredFolders.length === 0 && (
        <div className="text-center py-12">
          <Folder className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {searchQuery ? '找不到符合的資料夾' : '還沒有資料夾'}
          </h3>
          <p className="text-gray-500 mb-4">
            {searchQuery ? '試試其他關鍵字' : '建立第一個資料夾來整理您的書籤'}
          </p>
          {!searchQuery && (
            <button
              onClick={() => setShowCreateForm(true)}
              className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="h-4 w-4" />
              <span>新增資料夾</span>
            </button>
          )}
        </div>
      )}

      {/* 創建/編輯表單彈窗 */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="p-6">
              <h2 className="text-lg font-semibold mb-4">
                {editingFolder ? '編輯資料夾' : '新增資料夾'}
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    資料夾名稱
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="輸入資料夾名稱..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    資料夾顏色
                  </label>
                  <div className="grid grid-cols-6 gap-2">
                    {colorOptions.map(color => (
                      <button
                        key={color}
                        onClick={() => setFormData(prev => ({ ...prev, color }))}
                        className={`w-8 h-8 rounded-lg border-2 ${
                          formData.color === color ? 'border-gray-400' : 'border-gray-200'
                        }`}
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                </div>
                
                {!editingFolder?.is_default && (
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="is_default"
                      checked={formData.is_default}
                      onChange={(e) => setFormData(prev => ({ ...prev, is_default: e.target.checked }))}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="is_default" className="text-sm text-gray-700">
                      設為預設資料夾
                    </label>
                  </div>
                )}
              </div>
              
              <div className="flex gap-3 mt-6">
                <button
                  onClick={cancelEdit}
                  className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={editingFolder ? handleUpdateFolder : handleCreateFolder}
                  disabled={isCreating || !formData.name.trim()}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
                >
                  {isCreating && <Loader2 className="h-4 w-4 animate-spin" />}
                  {editingFolder ? '更新' : '創建'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FoldersContent;