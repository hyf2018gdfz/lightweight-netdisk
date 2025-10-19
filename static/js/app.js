/**
 * 个人网盘系统前端应用
 * 版本: 2.0 - 修复搜索功能，使用GET方法和地址栏搜索
 */

class NetdiskApp {
    constructor() {
        this.currentPath = '/';
        this.selectedFiles = new Set();
        this.accessToken = localStorage.getItem('access_token');
        this.userInfo = null;
        this.sortOrder = 'name-asc'; // 默认按名称升序排列
        this.isSearchResults = false; // 标记当前是否显示搜索结果
        
        this.init();
    }
    
    init() {
        // 检查登录状态
        if (this.accessToken) {
            this.checkAuth();
        } else {
            this.showLogin();
        }
        
        // 绑定事件
        this.bindEvents();
        
        // 初始化拖拽上传
        this.initDragUpload();
    }
    
    bindEvents() {
        // 登录表单
        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', this.handleLogin.bind(this));
        }
        
        // 文件上传
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.addEventListener('change', this.handleFileUpload.bind(this));
        }
        
        // 文件夹上传
        const folderInput = document.getElementById('folderInput');
        if (folderInput) {
            folderInput.addEventListener('change', this.handleFolderUpload.bind(this));
        }
        
        // 搜索
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.searchFiles();
                }
            });
        }
        
        // 模态框
        const modalOverlay = document.getElementById('modalOverlay');
        if (modalOverlay) {
            modalOverlay.addEventListener('click', (e) => {
                if (e.target === modalOverlay) {
                    this.closeModal();
                }
            });
        }
    }
    
    // 认证相关方法
    async checkAuth() {
        try {
            const response = await this.api('/auth/check');
            if (response.authenticated) {
                this.userInfo = response.user;
                this.showMainPage();
                this.initHistorySupport();
                // 恢复排序设置
                this.initSortOrder();
                // 从 URL 获取初始路径并加载相应内容
                this.currentPath = this.getPathFromUrl();
                if (this.currentPath === '/trash') {
                    this.showTrash(false); // 不更新 URL，因为已经在正确的 URL 上
                } else if (this.currentPath === '/shares') {
                    this.showShares(false); // 不更新 URL，因为已经在正确的 URL 上
                } else if (this.currentPath === '/search') {
                    // 处理搜索 URL
                    const urlParams = new URLSearchParams(window.location.search);
                    const keyword = urlParams.get('q');
                    if (keyword) {
                        document.getElementById('searchInput').value = keyword;
                        this.searchFiles(keyword);
                    } else {
                        this.loadFileList('/', false);
                    }
                } else {
                    this.loadFileList(this.currentPath, false); // 不更新 URL，因为已经在正确的 URL 上
                }
            } else {
                this.logout();
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            this.logout();
        }
    }
    
    async handleLogin(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        if (!username || !password) {
            this.showAlert('loginError', '请填写用户名和密码');
            return;
        }
        
        try {
            const loginBtn = document.getElementById('loginBtn');
            loginBtn.disabled = true;
            loginBtn.textContent = '登录中...';
            
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.accessToken = data.access_token;
                this.userInfo = data.user_info;
                localStorage.setItem('access_token', this.accessToken);
                localStorage.setItem('user_info', JSON.stringify(this.userInfo));
                
                this.showMainPage();
                this.initHistorySupport();
                // 恢复排序设置
                this.initSortOrder();
                // 从 URL 获取初始路径并加载相应内容
                this.currentPath = this.getPathFromUrl();
                if (this.currentPath === '/trash') {
                    this.showTrash(false); // 不更新 URL，因为已经在正确的 URL 上
                } else if (this.currentPath === '/shares') {
                    this.showShares(false); // 不更新 URL，因为已经在正确的 URL 上
                } else if (this.currentPath === '/search') {
                    // 处理搜索 URL
                    const urlParams = new URLSearchParams(window.location.search);
                    const keyword = urlParams.get('q');
                    if (keyword) {
                        document.getElementById('searchInput').value = keyword;
                        this.searchFiles(keyword);
                    } else {
                        this.loadFileList('/', false);
                    }
                } else {
                    this.loadFileList(this.currentPath, false); // 不更新 URL，因为已经在正确的 URL 上
                }
            } else {
                this.showAlert('loginError', data.detail || '登录失败');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showAlert('loginError', '网络错误，请稍后重试');
        } finally {
            const loginBtn = document.getElementById('loginBtn');
            loginBtn.disabled = false;
            loginBtn.textContent = '登录';
        }
    }
    
    logout() {
        this.accessToken = null;
        this.userInfo = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_info');
        this.showLogin();
    }
    
    showLogin() {
        document.getElementById('loginPage').style.display = 'flex';
        document.getElementById('mainPage').style.display = 'none';
    }
    
    showMainPage() {
        document.getElementById('loginPage').style.display = 'none';
        document.getElementById('mainPage').style.display = 'flex';
    }
    
    // API 请求方法
    async api(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        if (this.accessToken) {
            defaultOptions.headers['Authorization'] = `Bearer ${this.accessToken}`;
        }
        
        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers,
            },
        };
        
        const response = await fetch(url, mergedOptions);
        
        if (response.status === 401) {
            this.logout();
            throw new Error('Unauthorized');
        }
        
        return await response.json();
    }
    
    // 文件管理方法
    async loadFileList(path = this.currentPath, updateUrl = true) {
        try {
            this.showLoading(true);
            const data = await this.api(`/files/browse?path=${encodeURIComponent(path)}`);
            
            this.currentPath = data.path;
            this.isSearchResults = false; // 重置搜索状态
            this.updateBreadcrumb(data.path, data.parent_path);
            this.renderFileList(data.items);
            
            // 更新浏览器URL
            if (updateUrl) {
                this.updateUrl(path);
            }
            
        } catch (error) {
            console.error('Load file list error:', error);
            this.showAlert('error', '加载文件列表失败');
        } finally {
            this.showLoading(false);
        }
    }
    
    updateUrl(path) {
        const url = path === '/' ? '/' : path;
        window.history.pushState({path: path}, '', url);
    }
    
    // 从 URL 获取当前路径
    getPathFromUrl() {
        const pathname = window.location.pathname;
        if (pathname === '/') {
            return '/';
        }
        if (pathname === '/trash') {
            return '/trash';
        }
        if (pathname === '/shares') {
            return '/shares';
        }
        if (pathname === '/search') {
            return '/search';
        }
        // 其他路径都是文件夹路径
        return pathname;
    }
    
    initHistorySupport() {
        // 监听浏览器后退/前进按钮
        window.addEventListener('popstate', (event) => {
            if (event.state && event.state.path) {
                this.currentPath = event.state.path;
                if (this.currentPath === '/trash') {
                    this.showTrash(false); // 不更新 URL，因为已经在正确的 URL 上
                } else {
                    this.loadFileList(this.currentPath, false); // 不更新 URL，因为已经在正确的 URL 上
                }
            } else if (event.state && event.state.search) {
                // 处理搜索状态
                const keyword = event.state.search;
                document.getElementById('searchInput').value = keyword;
                this.searchFiles(keyword);
            } else {
                // 如果没有状态，从 URL 获取路径
                const path = this.getPathFromUrl();
                this.currentPath = path;
                if (path === '/trash') {
                    this.showTrash(false); // 不更新 URL，因为已经在正确的 URL 上
                } else if (path === '/shares') {
                    this.showShares(false); // 不更新 URL，因为已经在正确的 URL 上
                } else if (path === '/search') {
                    // 处理搜索 URL
                    const urlParams = new URLSearchParams(window.location.search);
                    const keyword = urlParams.get('q');
                    if (keyword) {
                        document.getElementById('searchInput').value = keyword;
                        this.searchFiles(keyword);
                    } else {
                        this.loadFileList('/', false);
                    }
                } else {
                    this.loadFileList(path, false);
                }
            }
        });
        
        // 设置初始状态
        window.history.replaceState({path: this.getPathFromUrl()}, '', window.location.pathname);
    }
    
    initSortOrder() {
        // 从本地存储恢复排序设置
        const savedSortOrder = localStorage.getItem('sortOrder');
        if (savedSortOrder) {
            this.sortOrder = savedSortOrder;
        }
        
        // 更新 UI 中的排序选择框
        const sortSelect = document.getElementById('sortSelect');
        if (sortSelect) {
            sortSelect.value = this.sortOrder;
        }
    }
    
    renderFileList(items) {
        const fileList = document.getElementById('fileList');
        const emptyState = document.getElementById('emptyState');
        
        if (items.length === 0) {
            fileList.innerHTML = ''; // 清空文件列表内容
            fileList.style.display = 'none';
            emptyState.innerHTML = `
                <i class="fas fa-folder-open"></i>
                <h3>文件夹为空</h3>
                <p>您可以上传文件或创建新文件夹</p>
            `;
            emptyState.style.display = 'block';
            return;
        }
        
        // 按排序设置排列文件
        const sortedItems = this.sortItems(items);
        
        fileList.style.display = 'block';
        emptyState.style.display = 'none';
        
        // 检查是否有同名文件（在搜索结果中或在不同路径下）
        const shouldShowFullPath = this.shouldShowFullPaths(sortedItems);
        fileList.innerHTML = sortedItems.map(item => this.renderFileItem(item, shouldShowFullPath)).join('');
        
        // 绑定文件项事件
        this.bindFileItemEvents();
    }
    
    sortItems(items) {
        const [sortBy, order] = this.sortOrder.split('-');
        
        return [...items].sort((a, b) => {
            let aValue, bValue;
            
            // 目录总是排在文件前面
            if (a.type !== b.type) {
                if (a.type === 'directory') return -1;
                if (b.type === 'directory') return 1;
            }
            
            switch (sortBy) {
                case 'name':
                    aValue = a.name.toLowerCase();
                    bValue = b.name.toLowerCase();
                    break;
                case 'date':
                    aValue = new Date(a.created_at).getTime();
                    bValue = new Date(b.created_at).getTime();
                    break;
                case 'size':
                    aValue = a.size || 0;
                    bValue = b.size || 0;
                    break;
                default:
                    aValue = a.name.toLowerCase();
                    bValue = b.name.toLowerCase();
            }
            
            if (aValue < bValue) {
                return order === 'asc' ? -1 : 1;
            }
            if (aValue > bValue) {
                return order === 'asc' ? 1 : -1;
            }
            return 0;
        });
    }
    
    changeSortOrder() {
        const sortSelect = document.getElementById('sortSelect');
        this.sortOrder = sortSelect.value;
        
        // 保存排序设置到本地存储
        localStorage.setItem('sortOrder', this.sortOrder);
        
        // 重新渲染当前文件列表
        this.loadFileList(this.currentPath, false);
    }
    
    shouldShowFullPaths(items) {
        // 如果是搜索结果，总是显示完整路径
        if (this.isSearchResults) {
            return true;
        }
        
        // 检查是否有同名文件在不同路径下
        const nameGroups = new Map();
        for (const item of items) {
            if (!nameGroups.has(item.name)) {
                nameGroups.set(item.name, []);
            }
            nameGroups.get(item.name).push(item);
        }
        
        // 如果有任何名称出现多次且在不同路径下，则显示完整路径
        for (const [name, group] of nameGroups) {
            if (group.length > 1) {
                const paths = new Set(group.map(item => item.path || item.full_path?.substring(0, item.full_path.lastIndexOf('/')) || '/'));
                if (paths.size > 1) {
                    return true;
                }
            }
        }
        
        return false;
    }
    
    renderFileItem(item, showFullPath = false) {
        const formattedSize = item.formatted_size || '';
        const createdAt = new Date(item.created_at).toLocaleDateString('zh-CN');
        
        // 如果在搜索结果中或需要显示完整路径，显示完整路径
        const displayName = (showFullPath && item.full_path) ? item.full_path : item.name;
        
        // 如果显示完整路径，在元数据中添加路径信息
        const pathInfo = showFullPath && item.path && item.path !== '/' && item.full_path !== item.name ?
            `<div class="file-path"><i class="fas fa-folder-open"></i> ${this.escapeHtml(item.path)}</div>` : '';
        
        return `
            <div class="file-item" data-id="${item.id}" data-name="${item.name}" data-type="${item.type}">
                <div class="file-icon">${item.icon}</div>
                <div class="file-info">
                    <div class="file-details">
                        <h4>${this.escapeHtml(displayName)}</h4>
                        ${pathInfo}
                        <div class="file-meta">
                            ${item.type === 'file' ? formattedSize + ' • ' : ''}${createdAt}
                        </div>
                    </div>
                    <div class="file-actions">
                        ${item.can_preview ? '<button class="action-btn" onclick="app.previewFile(' + item.id + ')"><i class="fas fa-eye"></i></button>' : ''}
                        <button class="action-btn" onclick="app.downloadFile(${item.id})"><i class="fas fa-download"></i></button>
                        <button class="action-btn" onclick="app.shareFile(${item.id})"><i class="fas fa-share-alt"></i></button>
                        <button class="action-btn" onclick="app.renameFile(${item.id}, '${this.escapeHtml(item.name)}')"><i class="fas fa-edit"></i></button>
                        <button class="action-btn" onclick="app.deleteFile(${item.id})"><i class="fas fa-trash"></i></button>
                    </div>
                </div>
            </div>
        `;
    }
    
    bindFileItemEvents() {
        const fileItems = document.querySelectorAll('.file-item');
        fileItems.forEach(item => {
            item.addEventListener('dblclick', () => {
                const type = item.dataset.type;
                const name = item.dataset.name;
                const id = item.dataset.id;
                
                if (type === 'directory') {
                    // 双击目录：进入目录
                    const newPath = this.currentPath === '/' ? `/${name}` : `${this.currentPath}/${name}`;
                    this.loadFileList(newPath);
                } else if (type === 'file') {
                    // 双击文件：预览文件
                    this.previewFile(parseInt(id));
                }
            });
            
            item.addEventListener('click', (e) => {
                if (e.target.closest('.file-actions')) return;
                
                // 文件选择逻辑
                if (e.ctrlKey || e.metaKey) {
                    item.classList.toggle('selected');
                } else {
                    document.querySelectorAll('.file-item.selected').forEach(selected => {
                        selected.classList.remove('selected');
                    });
                    item.classList.add('selected');
                }
            });
        });
    }
    
    updateBreadcrumb(currentPath, parentPath) {
        const breadcrumb = document.getElementById('breadcrumb');
        const parts = currentPath.split('/').filter(part => part);
        
        let html = '<span class="breadcrumb-item" data-path="/"><i class="fas fa-home"></i> 首页</span>';
        let path = '';
        
        parts.forEach(part => {
            path += '/' + part;
            const isActive = path === currentPath ? 'active' : '';
            html += `<span class="breadcrumb-item ${isActive}" data-path="${path}">${this.escapeHtml(part)}</span>`;
        });
        
        breadcrumb.innerHTML = html;
        
        // 绑定面包屑点击事件
        breadcrumb.querySelectorAll('.breadcrumb-item').forEach(item => {
            item.addEventListener('click', () => {
                const path = item.dataset.path;
                if (path === '/trash') {
                    this.showTrash();
                } else {
                    this.loadFileList(path);
                }
            });
        });
    }
    
    updateBreadcrumbForTrash() {
        const breadcrumb = document.getElementById('breadcrumb');
        breadcrumb.innerHTML = `
            <span class="breadcrumb-item" data-path="/"><i class="fas fa-home"></i> 首页</span>
            <span class="breadcrumb-item active" data-path="/trash"><i class="fas fa-trash"></i> 回收站</span>
        `;
        
        // 绑定面包屑点击事件
        breadcrumb.querySelectorAll('.breadcrumb-item').forEach(item => {
            item.addEventListener('click', () => {
                const path = item.dataset.path;
                if (path === '/trash') {
                    this.showTrash();
                } else {
                    this.loadFileList(path);
                }
            });
        });
    }
    
    // 文件操作方法
    uploadFiles() {
        document.getElementById('fileInput').click();
    }
    
    uploadFolder() {
        document.getElementById('folderInput').click();
    }
    
    async handleFileUpload(e) {
        const files = Array.from(e.target.files);
        if (files.length === 0) return;
        
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });
        formData.append('path', this.currentPath);
        
        try {
            this.showUploadProgress(true);
            
            const response = await fetch('/files/upload', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.accessToken}`,
                },
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert('success', data.message);
                this.loadFileList();
            } else {
                this.showAlert('error', data.message);
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showAlert('error', '上传失败');
        } finally {
            this.showUploadProgress(false);
            e.target.value = ''; // 清空文件选择
        }
    }
    
    async handleFolderUpload(e) {
        const files = Array.from(e.target.files);
        if (files.length === 0) return;
        
        // 获取文件相对路径
        const relativePaths = files.map(file => file.webkitRelativePath);
        
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });
        formData.append('path', this.currentPath);
        formData.append('relative_paths', JSON.stringify(relativePaths));
        
        try {
            this.showUploadProgress(true);
            
            const response = await fetch('/files/upload', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.accessToken}`,
                },
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert('success', data.message);
                this.loadFileList();
            } else {
                this.showAlert('error', data.message);
            }
        } catch (error) {
            console.error('Folder upload error:', error);
            this.showAlert('error', '文件夹上传失败');
        } finally {
            this.showUploadProgress(false);
            e.target.value = ''; // 清空文件选择
        }
    }
    
    async createFolder() {
        const folderName = prompt('请输入文件夹名称:');
        if (!folderName || !folderName.trim()) return;
        
        const path = this.currentPath === '/' ? `/${folderName.trim()}` : `${this.currentPath}/${folderName.trim()}`;
        
        try {
            const data = await this.api('/files/mkdir', {
                method: 'POST',
                body: JSON.stringify({ path })
            });
            
            if (data.success) {
                this.showAlert('success', data.message);
                this.loadFileList();
            } else {
                this.showAlert('error', data.message);
            }
        } catch (error) {
            console.error('Create folder error:', error);
            this.showAlert('error', '创建文件夹失败');
        }
    }
    
    async downloadFile(fileId) {
        try {
            const url = `/files/download/${fileId}`;
            const link = document.createElement('a');
            link.href = `${url}?token=${this.accessToken}`;
            link.download = '';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('Download error:', error);
            this.showAlert('error', '下载失败');
        }
    }
    
    async deleteFile(fileId) {
        if (!confirm('确定要删除这个文件吗？删除后将移入回收站。')) return;
        
        try {
            const data = await this.api(`/files/delete/${fileId}`, {
                method: 'DELETE'
            });
            
            if (data.success) {
                this.showAlert('success', data.message);
                this.loadFileList();
            } else {
                this.showAlert('error', data.message);
            }
        } catch (error) {
            console.error('Delete error:', error);
            this.showAlert('error', '删除失败');
        }
    }
    
    async renameFile(fileId, currentName) {
        const newName = prompt('请输入新名称:', currentName);
        if (!newName || newName === currentName) return;
        
        try {
            const data = await this.api(`/files/rename/${fileId}`, {
                method: 'PUT',
                body: JSON.stringify({ new_name: newName })
            });
            
            if (data.success) {
                this.showAlert('success', data.message);
                this.loadFileList();
            } else {
                this.showAlert('error', data.message);
            }
        } catch (error) {
            console.error('Rename error:', error);
            this.showAlert('error', '重命名失败');
        }
    }
    
    async previewFile(fileId) {
        try {
            const response = await fetch(`/files/preview/${fileId}`, {
                headers: {
                    'Authorization': `Bearer ${this.accessToken}`,
                }
            });
            
            if (response.ok) {
                const contentType = response.headers.get('content-type');
                
                if (contentType && contentType.startsWith('image/')) {
                    // 图片预览
                    const blob = await response.blob();
                    const imageUrl = URL.createObjectURL(blob);
                    this.showModal('图片预览', `<img src="${imageUrl}" class="preview-image" alt="预览图片">`);
                } else if (contentType && contentType.startsWith('audio/')) {
                    // 音频预览
                    const blob = await response.blob();
                    const audioUrl = URL.createObjectURL(blob);
                    this.showModal('音频预览', `
                        <div class="media-preview">
                            <audio controls style="width: 100%; max-width: 500px;">
                                <source src="${audioUrl}" type="${contentType}">
                                您的浏览器不支持音频播放。
                            </audio>
                        </div>
                    `);
                } else if (contentType && contentType.startsWith('video/')) {
                    // 视频预览
                    const blob = await response.blob();
                    const videoUrl = URL.createObjectURL(blob);
                    this.showModal('视频预览', `
                        <div class="media-preview">
                            <video controls style="width: 100%; max-width: 100%; max-height: 70vh;">
                                <source src="${videoUrl}" type="${contentType}">
                                您的浏览器不支持视频播放。
                            </video>
                        </div>
                    `);
                } else if (contentType && contentType === 'application/pdf') {
                    // PDF预览
                    const blob = await response.blob();
                    const pdfUrl = URL.createObjectURL(blob);
                    this.showModal('PDF预览', `
                        <div class="pdf-preview">
                            <iframe src="${pdfUrl}" style="width: 100%; height: 70vh; border: none;"></iframe>
                        </div>
                    `, `
                        <button type="button" class="btn btn-secondary" onclick="window.open('${pdfUrl}', '_blank')">在新窗口打开</button>
                        <button type="button" class="btn btn-primary" onclick="app.closeModal()">关闭</button>
                    `);
                } else {
                    // 文本预览
                    const data = await response.json();
                    this.showModal('文本预览', `<div class="preview-container"><pre class="preview-text">${this.escapeHtml(data.content)}</pre></div>`);
                }
            } else {
                this.showAlert('error', '预览失败');
            }
        } catch (error) {
            console.error('Preview error:', error);
            this.showAlert('error', '预览失败');
        }
    }
    
    async shareFile(fileId) {
        // 显示分享设置模态框
        const modalBody = `
            <form id="shareForm">
                <div class="form-group">
                    <label for="sharePassword">访问密码（可选）</label>
                    <input type="password" id="sharePassword" placeholder="留空表示无密码保护">
                </div>
                <div class="form-group">
                    <label for="shareExpireHours">过期时间（小时）</label>
                    <select id="shareExpireHours">
                        <option value="">永不过期</option>
                        <option value="1">1小时</option>
                        <option value="24">1天</option>
                        <option value="168">7天</option>
                        <option value="720">30天</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="shareDescription">分享描述（可选）</label>
                    <textarea id="shareDescription" rows="3" placeholder="告诉其他人这个文件的用途"></textarea>
                </div>
            </form>
        `;
        
        const modalFooter = `
            <button type="button" class="btn btn-ghost" onclick="app.closeModal()">取消</button>
            <button type="button" class="btn btn-primary" onclick="app.createShare(${fileId})">创建分享</button>
        `;
        
        this.showModal('创建分享链接', modalBody, modalFooter);
    }
    
    async createShare(fileId) {
        const password = document.getElementById('sharePassword').value;
        const expireHours = document.getElementById('shareExpireHours').value;
        const description = document.getElementById('shareDescription').value;
        
        const shareData = {
            file_node_id: fileId
        };
        
        if (password) shareData.password = password;
        if (expireHours) shareData.expire_hours = parseInt(expireHours);
        if (description) shareData.description = description;
        
        try {
            const data = await this.api('/share/create', {
                method: 'POST',
                body: JSON.stringify(shareData)
            });
            
            const shareUrl = `${window.location.origin}${data.share_url}`;
            
            const resultHtml = `
                <div class="alert alert-success">分享链接创建成功！</div>
                <div class="form-group">
                    <label>分享链接</label>
                    <input type="text" value="${shareUrl}" readonly onclick="this.select()">
                </div>
                <div class="form-group">
                    <label>分享ID</label>
                    <input type="text" value="${data.share_id}" readonly onclick="this.select()">
                </div>
                ${data.has_password ? '<p><strong>注意：</strong> 该分享链接需要密码访问</p>' : ''}
            `;
            
            const resultFooter = `
                <button type="button" class="btn btn-secondary" onclick="navigator.clipboard.writeText('${shareUrl}').then(() => app.showAlert('success', '链接已复制到剪贴板'))">复制链接</button>
                <button type="button" class="btn btn-primary" onclick="app.closeModal()">完成</button>
            `;
            
            this.showModal('分享链接已创建', resultHtml, resultFooter);
        } catch (error) {
            console.error('Create share error:', error);
            this.showAlert('error', '创建分享失败');
        }
    }
    
    async searchFiles(keyword = null) {
        if (keyword === null) {
            keyword = document.getElementById('searchInput').value.trim();
        }
        
        if (!keyword) {
            this.isSearchResults = false;
            this.loadFileList();
            return;
        }
        
        try {
            this.showLoading(true);
            const searchParams = new URLSearchParams({
                keyword: keyword,
                path: this.currentPath
            });
            
            const data = await this.api(`/files/search?${searchParams.toString()}`);
            
            this.isSearchResults = true;
            this.renderFileList(data.results);
            
            // 更新地址栏显示搜索参数
            const searchUrl = `/search?q=${encodeURIComponent(keyword)}`;
            window.history.pushState({search: keyword}, '', searchUrl);
            
            // 更新面包屑显示搜索结果
            const breadcrumb = document.getElementById('breadcrumb');
            breadcrumb.innerHTML = `<span class="breadcrumb-item active">搜索结果: "${this.escapeHtml(keyword)}" (${data.total}个)</span>`;
        } catch (error) {
            console.error('Search error:', error);
            this.showAlert('error', '搜索失败');
        } finally {
            this.showLoading(false);
        }
    }
    
    refreshFileList() {
        if (this.currentPath === '/trash') {
            this.showTrash(false); // 不更新 URL
        } else if (this.currentPath === '/shares') {
            this.showShares(false); // 不更新 URL
        } else {
            this.loadFileList();
        }
    }
    
    async showTrash(updateUrl = true) {
        try {
            this.showLoading(true);
            const data = await this.api('/trash/list');
            
            // 更新导航路径
            this.currentPath = '/trash';
            this.updateBreadcrumbForTrash();
            
            // 更新 URL（只有在需要时）
            if (updateUrl) {
                window.history.pushState({path: '/trash'}, '', '/trash');
            }
            
            // 渲染回收站文件列表
            this.renderTrashList(data.items);
            
        } catch (error) {
            console.error('Load trash error:', error);
            this.showAlert('error', '加载回收站失败');
        } finally {
            this.showLoading(false);
        }
    }
    
    renderTrashList(items) {
        const fileList = document.getElementById('fileList');
        const emptyState = document.getElementById('emptyState');
        
        if (items.length === 0) {
            fileList.innerHTML = '';
            emptyState.innerHTML = `
                <i class="fas fa-trash"></i>
                <h3>回收站为空</h3>
                <p>删除的文件将在此处显示</p>
            `;
            emptyState.style.display = 'block';
            return;
        }
        
        emptyState.style.display = 'none';
        
        fileList.innerHTML = `
            <div class="file-list-header">
                <div class="file-list-actions">
                    <button class="btn btn-primary" onclick="app.emptyTrash()">
                        <i class="fas fa-trash"></i> 清空回收站
                    </button>
                    <button class="btn btn-secondary" onclick="app.autoCleanTrash()">
                        <i class="fas fa-clock"></i> 清理过期文件
                    </button>
                </div>
            </div>
            <div class="file-grid">
                ${items.map(item => `
                    <div class="file-item">
                        <div class="file-icon">${item.icon}</div>
                        <div class="file-name">${item.name}</div>
                        <div class="file-info">
                            <span class="file-size">${item.formatted_size || ''}</span>
                            <span class="file-date">删除于 ${new Date(item.deleted_at).toLocaleString()}</span>
                            <span class="trash-days">剩余 ${item.days_remaining} 天</span>
                        </div>
                        <div class="file-actions">
                            <button class="action-btn" onclick="app.restoreFile(${item.id})" title="恢复">
                                <i class="fas fa-undo"></i>
                            </button>
                            <button class="action-btn danger" onclick="app.permanentDelete(${item.id})" title="永久删除">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    async restoreFile(nodeId) {
        try {
            const response = await fetch(`/trash/restore/${nodeId}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.accessToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert('success', data.message);
                this.showTrash(); // 刷新回收站列表
            } else {
                this.showAlert('error', data.message);
            }
        } catch (error) {
            console.error('Restore file error:', error);
            this.showAlert('error', '恢复文件失败');
        }
    }
    
    async permanentDelete(nodeId) {
        if (!confirm('确定要永久删除此文件吗？此操作无法撤销！')) {
            return;
        }
        
        try {
            const response = await fetch(`/trash/permanent/${nodeId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${this.accessToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert('success', data.message);
                this.showTrash(); // 刷新回收站列表
            } else {
                this.showAlert('error', data.message);
            }
        } catch (error) {
            console.error('Permanent delete error:', error);
            this.showAlert('error', '永久删除失败');
        }
    }
    
    async emptyTrash() {
        if (!confirm('确定要清空回收站吗？所有文件将被永久删除，此操作无法撤销！')) {
            return;
        }
        
        try {
            const response = await fetch('/trash/empty', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.accessToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert('success', data.message);
                this.showTrash(); // 刷新回收站列表
            } else {
                this.showAlert('error', data.message);
            }
        } catch (error) {
            console.error('Empty trash error:', error);
            this.showAlert('error', '清空回收站失败');
        }
    }
    
    async autoCleanTrash() {
        try {
            const response = await fetch('/trash/auto-clean', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.accessToken}`,
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert('success', data.message);
                this.showTrash(); // 刷新回收站列表
            } else {
                this.showAlert('error', data.message);
            }
        } catch (error) {
            console.error('Auto clean trash error:', error);
            this.showAlert('error', '自动清理失败');
        }
    }
    
    async showShares(updateUrl = true) {
        try {
            this.showLoading(true);
            const data = await this.api('/share/list');
            
            // 更新导航路径
            this.currentPath = '/shares';
            this.updateBreadcrumbForShares();
            
            // 更新 URL（只有在需要时）
            if (updateUrl) {
                window.history.pushState({path: '/shares'}, '', '/shares');
            }
            
            // 渲染分享列表
            this.renderShareList(data.shares);
            
        } catch (error) {
            console.error('Load shares error:', error);
            this.showAlert('error', '加载分享列表失败');
        } finally {
            this.showLoading(false);
        }
    }
    
    updateBreadcrumbForShares() {
        const breadcrumb = document.getElementById('breadcrumb');
        breadcrumb.innerHTML = `
            <span class="breadcrumb-item active">
                <i class="fas fa-share-alt"></i> 我的分享
            </span>
        `;
    }
    
    renderShareList(shares) {
        const fileList = document.getElementById('fileList');
        const emptyState = document.getElementById('emptyState');
        
        if (shares.length === 0) {
            fileList.innerHTML = '';
            emptyState.innerHTML = `
                <i class="fas fa-share-alt"></i>
                <h3>暂无分享</h3>
                <p>您可以在文件列表中选择文件进行分享</p>
            `;
            emptyState.style.display = 'flex';
            return;
        }
        
        emptyState.style.display = 'none';
        
        let html = '';
        shares.forEach(share => {
            const shareInfo = share.file_info;
            if (!shareInfo) return;
            
            const isExpired = share.is_expired;
            const isActive = share.is_active && !isExpired;
            const statusClass = isActive ? 'status-active' : (isExpired ? 'status-expired' : 'status-inactive');
            const statusText = isActive ? '有效' : (isExpired ? '已过期' : '已停用');
            
            const createdTime = new Date(share.created_at).toLocaleString('zh-CN');
            const expireTime = share.expire_at ? new Date(share.expire_at).toLocaleString('zh-CN') : '永不过期';
            
            html += `
                <div class="file-item share-item" data-share-id="${share.share_id}">
                    <div class="file-info">
                        <div class="file-icon">${shareInfo.icon}</div>
                        <div class="file-details">
                            <div class="file-name">${this.escapeHtml(shareInfo.name)}</div>
                            <div class="file-meta">
                                <span class="share-status ${statusClass}">${statusText}</span>
                                <span>• 下载: ${share.current_downloads}${share.max_downloads ? '/' + share.max_downloads : ''}</span>
                                ${share.has_password ? '<span>• <i class="fas fa-lock"></i> 加密</span>' : ''}
                            </div>
                            <div class="file-meta">
                                <span>创建: ${createdTime}</span>
                                <span>• 过期: ${expireTime}</span>
                            </div>
                            ${share.description ? `<div class="share-description">${this.escapeHtml(share.description)}</div>` : ''}
                        </div>
                    </div>
                    <div class="file-actions">
                        <button class="btn btn-sm btn-ghost" onclick="app.copyShareLink('${share.share_id}')"
                                title="复制链接">
                            <i class="fas fa-copy"></i>
                        </button>
                        <button class="btn btn-sm btn-ghost" onclick="app.viewShareStats('${share.share_id}')"
                                title="查看统计">
                            <i class="fas fa-chart-bar"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="app.deleteShare('${share.share_id}')"
                                title="删除分享">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        });
        
        fileList.innerHTML = html;
    }
    
    async copyShareLink(shareId) {
        const shareUrl = `${window.location.origin}/share/${shareId}`;
        try {
            await navigator.clipboard.writeText(shareUrl);
            this.showAlert('success', '分享链接已复制到剪贴板');
        } catch (error) {
            console.error('Copy error:', error);
            this.showAlert('error', '复制失败');
        }
    }
    
    async viewShareStats(shareId) {
        // TODO: 实现分享统计查看
        this.showAlert('info', '分享统计功能开发中');
    }
    
    async deleteShare(shareId) {
        if (!confirm('确定要删除这个分享吗？删除后将无法通过链接访问。')) return;
        
        try {
            const data = await this.api(`/share/delete/${shareId}`, {
                method: 'DELETE'
            });
            
            if (data.success) {
                this.showAlert('success', data.message);
                this.showShares(false); // 重新加载列表
            } else {
                this.showAlert('error', data.message);
            }
        } catch (error) {
            console.error('Delete share error:', error);
            this.showAlert('error', '删除分享失败');
        }
    }
    
    // 拖拽上传
    initDragUpload() {
        const mainContent = document.querySelector('.main-content');
        if (!mainContent) return;
        
        let dragCounter = 0;
        
        mainContent.addEventListener('dragenter', (e) => {
            e.preventDefault();
            dragCounter++;
            if (dragCounter === 1) {
                mainContent.classList.add('drag-over');
                this.showDragOverlay(true);
            }
        });
        
        mainContent.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dragCounter--;
            if (dragCounter === 0) {
                mainContent.classList.remove('drag-over');
                this.showDragOverlay(false);
            }
        });
        
        mainContent.addEventListener('dragover', (e) => {
            e.preventDefault();
        });
        
        mainContent.addEventListener('drop', (e) => {
            e.preventDefault();
            dragCounter = 0;
            mainContent.classList.remove('drag-over');
            this.showDragOverlay(false);
            
            const files = Array.from(e.dataTransfer.files);
            if (files.length > 0) {
                this.handleDragUpload(files);
            }
        });
    }
    
    async handleDragUpload(files) {
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });
        formData.append('path', this.currentPath);
        
        try {
            this.showUploadProgress(true, `上传 ${files.length} 个文件...`);
            
            const response = await fetch('/files/upload', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.accessToken}`,
                },
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showAlert('success', data.message);
                this.loadFileList();
            } else {
                this.showAlert('error', data.message);
            }
        } catch (error) {
            console.error('Drag upload error:', error);
            this.showAlert('error', '拖拽上传失败');
        } finally {
            this.showUploadProgress(false);
        }
    }
    
    showDragOverlay(show) {
        let overlay = document.getElementById('dragOverlay');
        if (show && !overlay) {
            overlay = document.createElement('div');
            overlay.id = 'dragOverlay';
            overlay.className = 'drag-overlay';
            overlay.innerHTML = '<div><i class="fas fa-cloud-upload-alt"></i><br>释放文件以上传</div>';
            document.querySelector('.main-content').appendChild(overlay);
        } else if (!show && overlay) {
            overlay.remove();
        }
    }
    
    // UI 辅助方法
    showLoading(show) {
        const loading = document.getElementById('fileListLoading');
        const fileList = document.getElementById('fileList');
        
        if (show) {
            loading.style.display = 'flex';
            fileList.style.display = 'none';
        } else {
            loading.style.display = 'none';
            fileList.style.display = 'block';
        }
    }
    
    showUploadProgress(show, text = '上传中...') {
        const uploadProgress = document.getElementById('uploadProgress');
        const uploadText = document.getElementById('uploadText');
        
        if (show) {
            uploadText.textContent = text;
            uploadProgress.style.display = 'block';
        } else {
            uploadProgress.style.display = 'none';
        }
    }
    
    hideUploadProgress() {
        this.showUploadProgress(false);
    }
    
    showModal(title, body, footer = '') {
        const modal = document.getElementById('modalOverlay');
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');
        const modalFooter = document.getElementById('modalFooter');
        
        modalTitle.textContent = title;
        modalBody.innerHTML = body;
        modalFooter.innerHTML = footer;
        modal.style.display = 'flex';
    }
    
    closeModal() {
        document.getElementById('modalOverlay').style.display = 'none';
    }
    
    showAlert(type, message) {
        // 创建浮动提示
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        alert.style.position = 'fixed';
        alert.style.top = '20px';
        alert.style.right = '20px';
        alert.style.zIndex = '1001';
        alert.style.display = 'block';
        alert.style.minWidth = '300px';
        
        document.body.appendChild(alert);
        
        // 3秒后自动消失
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 3000);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 全局函数绑定
window.uploadFiles = () => app.uploadFiles();
window.uploadFolder = () => app.uploadFolder();
window.createFolder = () => app.createFolder();
window.refreshFileList = () => app.refreshFileList();
window.showTrash = () => app.showTrash();
window.showShares = () => app.showShares();
window.searchFiles = () => app.searchFiles();
window.logout = () => app.logout();
window.closeModal = () => app.closeModal();

// 初始化应用
const app = new NetdiskApp();