/**
 * 个人网盘系统前端应用
 */

class NetdiskApp {
    constructor() {
        this.currentPath = '/';
        this.selectedFiles = new Set();
        this.accessToken = localStorage.getItem('access_token');
        this.userInfo = null;
        
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
                this.loadFileList();
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
                this.loadFileList();
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
    async loadFileList(path = this.currentPath) {
        try {
            this.showLoading(true);
            const data = await this.api(`/files/browse?path=${encodeURIComponent(path)}`);
            
            this.currentPath = data.path;
            this.updateBreadcrumb(data.path, data.parent_path);
            this.renderFileList(data.items);
            
        } catch (error) {
            console.error('Load file list error:', error);
            this.showAlert('error', '加载文件列表失败');
        } finally {
            this.showLoading(false);
        }
    }
    
    renderFileList(items) {
        const fileList = document.getElementById('fileList');
        const emptyState = document.getElementById('emptyState');
        
        if (items.length === 0) {
            fileList.style.display = 'none';
            emptyState.style.display = 'block';
            return;
        }
        
        fileList.style.display = 'block';
        emptyState.style.display = 'none';
        
        fileList.innerHTML = items.map(item => this.renderFileItem(item)).join('');
        
        // 绑定文件项事件
        this.bindFileItemEvents();
    }
    
    renderFileItem(item) {
        const formattedSize = item.formatted_size || '';
        const createdAt = new Date(item.created_at).toLocaleDateString('zh-CN');
        
        return `
            <div class="file-item" data-id="${item.id}" data-name="${item.name}" data-type="${item.type}">
                <div class="file-icon">${item.icon}</div>
                <div class="file-info">
                    <div class="file-details">
                        <h4>${this.escapeHtml(item.name)}</h4>
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
                
                if (type === 'directory') {
                    const newPath = this.currentPath === '/' ? `/${name}` : `${this.currentPath}/${name}`;
                    this.loadFileList(newPath);
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
                this.loadFileList(path);
            });
        });
    }
    
    // 文件操作方法
    uploadFiles() {
        document.getElementById('fileInput').click();
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
                    this.showModal('文件预览', `<img src="${imageUrl}" class="preview-image" alt="预览图片">`);
                } else {
                    // 文本预览
                    const data = await response.json();
                    this.showModal('文件预览', `<div class="preview-container"><pre class="preview-text">${this.escapeHtml(data.content)}</pre></div>`);
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
    
    async searchFiles() {
        const keyword = document.getElementById('searchInput').value.trim();
        if (!keyword) {
            this.loadFileList();
            return;
        }
        
        try {
            this.showLoading(true);
            const data = await this.api('/files/search', {
                method: 'POST',
                body: JSON.stringify({
                    keyword: keyword,
                    path: this.currentPath
                })
            });
            
            this.renderFileList(data.results);
            
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
        this.loadFileList();
    }
    
    showTrash() {
        // TODO: 实现回收站页面
        this.showAlert('info', '回收站功能开发中');
    }
    
    showShares() {
        // TODO: 实现分享管理页面
        this.showAlert('info', '分享管理功能开发中');
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
window.createFolder = () => app.createFolder();
window.refreshFileList = () => app.refreshFileList();
window.showTrash = () => app.showTrash();
window.showShares = () => app.showShares();
window.searchFiles = () => app.searchFiles();
window.logout = () => app.logout();
window.closeModal = () => app.closeModal();

// 初始化应用
const app = new NetdiskApp();