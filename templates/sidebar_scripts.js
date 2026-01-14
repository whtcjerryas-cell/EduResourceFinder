// ==================== 侧边栏折叠功能 ====================

let sidebarCollapsed = false;

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebarToggle');
    const mainContent = document.getElementById('mainContent');

    sidebarCollapsed = !sidebarCollapsed;

    if (sidebarCollapsed) {
        sidebar.classList.add('collapsed');
        toggle.classList.add('collapsed');
        if (mainContent) {
            mainContent.classList.add('expanded');
        }
    } else {
        sidebar.classList.remove('collapsed');
        toggle.classList.remove('collapsed');
        if (mainContent) {
            mainContent.classList.remove('expanded');
        }
    }

    // 保存状态到localStorage
    try {
        localStorage.setItem('sidebarCollapsed', sidebarCollapsed);
    } catch (e) {
        console.warn('无法保存侧边栏状态:', e);
    }
}

// 页面加载时恢复侧边栏状态
window.addEventListener('DOMContentLoaded', function() {
    try {
        const savedState = localStorage.getItem('sidebarCollapsed');
        if (savedState === 'true') {
            sidebarCollapsed = false; // 将在toggleSidebar中翻转
            toggleSidebar();
        }
    } catch (e) {
        console.warn('无法恢复侧边栏状态:', e);
    }
});
