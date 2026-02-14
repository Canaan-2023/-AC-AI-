/**
 * AbyssAC 前端应用
 */

// ==================== 全局状态 ====================
let currentSessionId = localStorage.getItem('abyssac_session_id') || null;
let sessions = {};
let currentTaskId = null;
let isProcessing = false;

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    // 更新时间
    updateTime();
    setInterval(updateTime, 1000);
    
    // 初始化会话
    await initSession();
    
    // 加载数据
    await loadNNGTree();
    await loadMemoryStats();
    await loadDMNLogs();
    
    // 绑定事件
    bindEvents();
    
    // 启动轮询
    startPolling();
}

function updateTime() {
    const now = new Date();
    document.getElementById('currentTime').textContent = 
        now.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
}

// ==================== 会话管理 ====================
async function initSession() {
    if (!currentSessionId) {
        await createNewSession();
    } else {
        // 验证会话是否有效
        const history = await fetchSessionHistory(currentSessionId);
        if (history === null) {
            await createNewSession();
        } else {
            renderChatHistory(history);
        }
    }
    await updateSessionSelector();
}

async function createNewSession() {
    try {
        const response = await fetch('/api/session/new', { method: 'POST' });
        const data = await response.json();
        currentSessionId = data.session_id;
        localStorage.setItem('abyssac_session_id', currentSessionId);
        sessions[currentSessionId] = data;
        
        // 清空对话历史
        document.getElementById('chatHistory').innerHTML = 
            '<div class="text-muted text-center py-4">暂无对话</div>';
        
        await updateSessionSelector();
        showNotification('新会话已创建', 'success');
    } catch (error) {
        console.error('创建会话失败:', error);
        showNotification('创建会话失败', 'error');
    }
}

async function updateSessionSelector() {
    try {
        const response = await fetch('/api/session/list');
        const data = await response.json();
        
        const selector = document.getElementById('sessionSelector');
        selector.innerHTML = '<option value="">选择会话...</option>';
        
        data.sessions.forEach(session => {
            const option = document.createElement('option');
            option.value = session.session_id;
            const date = new Date(session.created_at);
            const isCurrent = session.session_id === currentSessionId;
            option.textContent = `会话 ${date.toLocaleString('zh-CN')} ${isCurrent ? '(当前)' : ''}`;
            if (isCurrent) option.selected = true;
            selector.appendChild(option);
        });
    } catch (error) {
        console.error('获取会话列表失败:', error);
    }
}

async function fetchSessionHistory(sessionId) {
    try {
        const response = await fetch(`/api/session/history?session_id=${sessionId}&count=20`);
        if (!response.ok) return null;
        const data = await response.json();
        return data.history;
    } catch (error) {
        console.error('获取会话历史失败:', error);
        return null;
    }
}

function renderChatHistory(history) {
    const container = document.getElementById('chatHistory');
    
    if (!history || history.length === 0) {
        container.innerHTML = '<div class="text-muted text-center py-4">暂无对话</div>';
        return;
    }
    
    container.innerHTML = '';
    history.forEach(msg => {
        const div = document.createElement('div');
        div.className = `chat-message ${msg.role}`;
        div.innerHTML = `<strong>${msg.role === 'user' ? '用户' : 'AI'}:</strong> ${escapeHtml(msg.content)}`;
        container.appendChild(div);
    });
    
    container.scrollTop = container.scrollHeight;
}

// ==================== 事件绑定 ====================
function bindEvents() {
    // 发送消息
    document.getElementById('sendBtn').addEventListener('click', sendMessage);
    document.getElementById('userInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 新建会话
    document.getElementById('newSessionBtn').addEventListener('click', createNewSession);
    
    // 会话切换
    document.getElementById('sessionSelector').addEventListener('change', async (e) => {
        const sessionId = e.target.value;
        if (sessionId) {
            currentSessionId = sessionId;
            localStorage.setItem('abyssac_session_id', sessionId);
            const history = await fetchSessionHistory(sessionId);
            renderChatHistory(history);
            await updateSessionSelector();
        }
    });
    
    // 启动DMN
    document.getElementById('startDMN').addEventListener('click', async () => {
        const taskType = document.getElementById('dmnTaskTypeSelect').value;
        await triggerDMN(taskType);
        
        // 关闭模态框
        const modal = bootstrap.Modal.getInstance(document.getElementById('dmnModal'));
        modal.hide();
    });
}

// ==================== 消息发送 ====================
async function sendMessage() {
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    
    if (!message || isProcessing) return;
    if (!currentSessionId) {
        showNotification('请先创建会话', 'warning');
        return;
    }
    
    isProcessing = true;
    input.value = '';
    
    // 添加用户消息到界面
    addMessageToUI('user', message);
    
    // 更新沙盒状态
    updateSandboxStatus('processing', 1);
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                input: message
            })
        });
        
        const data = await response.json();
        currentTaskId = data.task_id;
        
        // 开始轮询结果
        pollTaskResult(currentTaskId);
        
    } catch (error) {
        console.error('发送消息失败:', error);
        showNotification('发送消息失败', 'error');
        isProcessing = false;
        updateSandboxStatus('idle', 1);
    }
}

function addMessageToUI(role, content) {
    const container = document.getElementById('chatHistory');
    
    // 移除"暂无对话"提示
    if (container.querySelector('.text-muted')) {
        container.innerHTML = '';
    }
    
    const div = document.createElement('div');
    div.className = `chat-message ${role}`;
    div.innerHTML = `<strong>${role === 'user' ? '用户' : 'AI'}:</strong> ${escapeHtml(content)}`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

async function pollTaskResult(taskId) {
    const maxAttempts = 60; // 最多轮询60次（1分钟）
    let attempts = 0;
    
    const interval = setInterval(async () => {
        attempts++;
        
        try {
            const response = await fetch(`/api/sandbox/status/${taskId}?session_id=${currentSessionId}`);
            const status = await response.json();
            
            // 更新沙盒UI
            updateSandboxUI(status);
            
            if (status.completed || attempts >= maxAttempts) {
                clearInterval(interval);
                isProcessing = false;
                
                if (status.completed) {
                    // 刷新对话历史
                    const history = await fetchSessionHistory(currentSessionId);
                    renderChatHistory(history);
                    updateSandboxStatus('completed', 3);
                } else {
                    showNotification('处理超时', 'warning');
                    updateSandboxStatus('idle', 1);
                }
            }
        } catch (error) {
            console.error('轮询任务状态失败:', error);
            clearInterval(interval);
            isProcessing = false;
            updateSandboxStatus('error', 1);
        }
    }, 1000);
}

// ==================== 沙盒UI更新 ====================
function updateSandboxUI(status) {
    const steps = document.querySelectorAll('#sandboxSteps .step-item');
    
    // 更新步骤状态
    steps.forEach((step, index) => {
        step.classList.remove('active', 'completed', 'error');
        
        if (index < status.currentLayer - 1) {
            step.classList.add('completed');
        } else if (index === status.currentLayer - 1) {
            step.classList.add('active');
        }
    });
    
    // 更新详情
    const detail = document.getElementById('sandboxDetail');
    if (status.path) {
        detail.innerHTML = `
            <div><strong>导航路径:</strong> ${status.path.join(' → ')}</div>
            <div><strong>当前节点:</strong> ${status.currentNode}</div>
            ${status.selectedMemories && status.selectedMemories.length > 0 ? 
                `<div class="mt-2"><strong>选中记忆:</strong> ${status.selectedMemories.length} 条</div>` : ''}
        `;
    }
    
    // 更新位置信息
    if (status.path) {
        document.getElementById('currentPosition').textContent = status.currentNode;
        document.getElementById('currentDepth').textContent = status.path.length - 1;
    }
}

function updateSandboxStatus(state, layer) {
    const steps = document.querySelectorAll('#sandboxSteps .step-item');
    const statusBadge = document.getElementById('systemStatus');
    
    if (state === 'processing') {
        statusBadge.className = 'badge bg-warning status-badge';
        statusBadge.textContent = '处理中...';
    } else if (state === 'completed') {
        statusBadge.className = 'badge bg-success status-badge';
        statusBadge.textContent = '系统空闲';
    } else if (state === 'error') {
        statusBadge.className = 'badge bg-danger status-badge';
        statusBadge.textContent = '错误';
    } else {
        statusBadge.className = 'badge bg-success status-badge';
        statusBadge.textContent = '系统空闲';
    }
    
    steps.forEach((step, index) => {
        step.classList.remove('active', 'completed');
        if (index < layer - 1) {
            step.classList.add('completed');
        } else if (index === layer - 1) {
            step.classList.add('active');
        }
    });
}

// ==================== NNG树 ====================
async function loadNNGTree() {
    try {
        const response = await fetch('/api/nng/tree');
        const data = await response.json();
        renderNNGTree(data.nodes);
    } catch (error) {
        console.error('加载NNG树失败:', error);
        document.getElementById('nngTree').innerHTML = 
            '<div class="text-danger text-center">加载失败</div>';
    }
}

function renderNNGTree(nodes, container = null, level = 0) {
    if (!container) {
        container = document.getElementById('nngTree');
        container.innerHTML = '';
    }
    
    if (!nodes || nodes.length === 0) {
        if (level === 0) {
            container.innerHTML = '<div class="text-muted text-center">NNG树为空</div>';
        }
        return;
    }
    
    nodes.forEach(node => {
        const item = document.createElement('div');
        item.className = 'nng-tree-item';
        item.innerHTML = `
            <span class="text-primary">${node.id}</span>
            <span class="text-muted">- ${escapeHtml(node.content || '无描述')}</span>
            ${node.memory_count > 0 ? `<span class="badge bg-info ms-1">${node.memory_count}</span>` : ''}
        `;
        item.addEventListener('click', () => showNNGDetail(node.id));
        container.appendChild(item);
        
        if (node.children && node.children.length > 0) {
            const childrenContainer = document.createElement('div');
            childrenContainer.className = 'nng-tree-children';
            container.appendChild(childrenContainer);
            renderNNGTree(node.children, childrenContainer, level + 1);
        }
    });
}

async function showNNGDetail(nodeId) {
    try {
        const response = await fetch(`/api/nng/node/${nodeId}`);
        const data = await response.json();
        
        // 可以在这里显示节点详情弹窗
        console.log('NNG节点详情:', data);
    } catch (error) {
        console.error('获取节点详情失败:', error);
    }
}

// ==================== 记忆统计 ====================
async function loadMemoryStats() {
    try {
        const response = await fetch('/api/memories/stats');
        const data = await response.json();
        
        document.getElementById('totalMemories').textContent = data.total || 0;
        document.getElementById('highValueMemories').textContent = data.high_value || 0;
        document.getElementById('workingMemories').textContent = data.working || 0;
    } catch (error) {
        console.error('加载记忆统计失败:', error);
    }
}

// ==================== DMN ====================
async function triggerDMN(taskType) {
    try {
        const response = await fetch('/api/dmn/trigger', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_type: taskType })
        });
        
        const data = await response.json();
        
        if (data.status === 'started') {
            showNotification('DMN任务已启动', 'success');
        } else {
            showNotification(`DMN任务启动失败: ${data.result?.error || '未知错误'}`, 'error');
        }
    } catch (error) {
        console.error('启动DMN任务失败:', error);
        showNotification('启动DMN任务失败', 'error');
    }
}

async function loadDMNLogs() {
    try {
        const response = await fetch('/api/dmn/logs?limit=5');
        const data = await response.json();
        
        const container = document.getElementById('dmnLogs');
        
        if (!data.logs || data.logs.length === 0) {
            container.innerHTML = '<li class="list-group-item text-muted">暂无日志</li>';
            return;
        }
        
        container.innerHTML = '';
        data.logs.forEach(log => {
            const li = document.createElement('li');
            li.className = 'list-group-item log-item';
            const time = new Date(log.completed_at || log.started_at);
            li.textContent = `${time.toLocaleTimeString()} - ${log.task_type || '未知任务'}`;
            container.appendChild(li);
        });
    } catch (error) {
        console.error('加载DMN日志失败:', error);
    }
}

async function updateDMNStatus() {
    try {
        const response = await fetch('/api/dmn/status');
        const data = await response.json();
        
        const statusBadge = document.getElementById('dmnStatus');
        const taskInfo = document.getElementById('currentDMNTask');
        const progressBar = document.getElementById('dmnProgress');
        
        if (data.is_running) {
            statusBadge.className = 'badge bg-warning';
            statusBadge.textContent = '运行中';
            
            taskInfo.style.display = 'block';
            document.getElementById('dmnTaskType').textContent = 
                `当前任务: ${data.current_task?.type || '未知'}`;
            document.getElementById('dmnAgent').textContent = 
                `agent ${data.current_task?.current_agent || 0}/5`;
            
            const progress = data.current_task?.progress || 0;
            progressBar.style.width = `${progress}%`;
            progressBar.textContent = `${progress}%`;
        } else {
            statusBadge.className = 'badge bg-secondary';
            statusBadge.textContent = '未运行';
            taskInfo.style.display = 'none';
            progressBar.style.width = '0%';
            progressBar.textContent = '0%';
        }
    } catch (error) {
        console.error('更新DMN状态失败:', error);
    }
}

// ==================== 轮询 ====================
function startPolling() {
    // 每3秒更新DMN状态
    setInterval(updateDMNStatus, 3000);
    
    // 每30秒刷新NNG树和记忆统计
    setInterval(() => {
        loadNNGTree();
        loadMemoryStats();
    }, 30000);
    
    // 每10秒刷新DMN日志
    setInterval(loadDMNLogs, 10000);
}

// ==================== 工具函数 ====================
function showNotification(message, type = 'info') {
    const notificationRow = document.getElementById('notificationRow');
    const notificationBar = document.getElementById('notificationBar');
    
    notificationBar.className = `alert alert-${type} mb-0`;
    notificationBar.textContent = message;
    notificationRow.style.display = 'block';
    
    setTimeout(() => {
        notificationRow.style.display = 'none';
    }, 5000);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
