/**
 * Base Scripts - K12教育资源搜索系统
 * 核心JavaScript功能：Toast通知、侧边栏切换、移动端菜单
 */

// ========== Toast通知系统 ==========
function showToast(type, title, message, duration = 3000) {
    const container = document.getElementById('toastContainer');
    if (!container) {
        console.error('Toast容器未找到');
        return;
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.setAttribute('role', 'alert');

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || 'ℹ️'}</div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <div class="toast-progress" style="animation-duration: ${duration}ms"></div>
    `;

    container.appendChild(toast);

    // 自动移除Toast
    setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => {
            if (container.contains(toast)) {
                container.removeChild(toast);
            }
        }, 300);
    }, duration);
}

// ========== ToastManager类 ==========
class ToastManager {
    constructor() {
        this.container = document.getElementById('toastContainer');
    }

    show(options) {
        const {
            type = 'info',
            title = '',
            message = '',
            duration = 3000
        } = options;

        showToast(type, title, message, duration);
    }

    success(title, message, duration) {
        this.show({ type: 'success', title, message, duration });
    }

    error(title, message, duration) {
        this.show({ type: 'error', title, message, duration });
    }

    warning(title, message, duration) {
        this.show({ type: 'warning', title, message, duration });
    }

    info(title, message, duration) {
        this.show({ type: 'info', title, message, duration });
    }
}

// 全局Toast实例
const toast = new ToastManager();

// ========== 侧边栏功能 ==========
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    const isMobile = window.innerWidth <= 768;

    if (!sidebar || !mainContent) {
        console.error('侧边栏或主内容区未找到');
        return;
    }

    if (isMobile) {
        toggleMobileMenu();
    } else {
        // 桌面端：折叠/展开侧边栏
        window.sidebarCollapsed = !window.sidebarCollapsed;

        if (window.sidebarCollapsed) {
            sidebar.classList.add('collapsed');
            mainContent.classList.add('expanded');
        } else {
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('expanded');
        }

        // 保存状态到localStorage
        localStorage.setItem('sidebarCollapsed', window.sidebarCollapsed);
    }
}

// ========== 移动端菜单功能 ==========
function toggleMobileMenu() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const menuButton = document.getElementById('mobileMenuButton');

    if (!sidebar || !overlay || !menuButton) {
        console.error('移动菜单元素未找到');
        return;
    }

    window.mobileMenuOpen = !window.mobileMenuOpen;

    if (window.mobileMenuOpen) {
        // 打开菜单
        sidebar.classList.add('mobile-open');
        overlay.classList.add('active');
        menuButton.classList.add('active');
        menuButton.setAttribute('aria-label', '关闭菜单');
        menuButton.setAttribute('aria-expanded', 'true');
        document.body.style.overflow = 'hidden';
    } else {
        // 关闭菜单
        sidebar.classList.remove('mobile-open');
        overlay.classList.remove('active');
        menuButton.classList.remove('active');
        menuButton.setAttribute('aria-label', '打开菜单');
        menuButton.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
    }
}

// ========== 初始化函数 ==========
function initializeBaseComponents() {
    console.log('🔧 初始化基础组件...');

    // 初始化全局状态
    window.sidebarCollapsed = false;
    window.mobileMenuOpen = false;

    // 恢复侧边栏状态
    const savedSidebarState = localStorage.getItem('sidebarCollapsed');
    if (savedSidebarState === 'true') {
        window.sidebarCollapsed = false;
        toggleSidebar();
    }

    // 绑定侧边栏切换按钮
    const toggleBtn = document.getElementById('sidebarToggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            toggleSidebar();
        });
    }

    // 绑定移动端菜单按钮
    const mobileMenuBtn = document.getElementById('mobileMenuButton');
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', function(e) {
            e.preventDefault();
            toggleMobileMenu();
        });
    }

    // 绑定遮罩层点击
    const overlay = document.getElementById('sidebarOverlay');
    if (overlay) {
        overlay.addEventListener('click', function() {
            if (window.mobileMenuOpen) {
                toggleMobileMenu();
            }
        });
    }

    // 修复导航链接点击（移动端自动关闭菜单）
    const navLinks = document.querySelectorAll('.sidebar-nav-item');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const isMobile = window.innerWidth <= 768;
            if (isMobile && window.mobileMenuOpen) {
                e.preventDefault();
                toggleMobileMenu();
                setTimeout(() => {
                    window.location.href = this.href;
                }, 300);
            }
        });
    });

    // 键盘快捷键
    document.addEventListener('keydown', function(event) {
        // Ctrl+B 或 Cmd+B 切换侧边栏
        if ((event.ctrlKey || event.metaKey) && event.key === 'b') {
            event.preventDefault();
            toggleSidebar();
        }

        // Escape 键关闭移动菜单
        if (event.key === 'Escape' && window.mobileMenuOpen) {
            toggleMobileMenu();
        }
    });

    // 窗口大小变化时重置移动菜单状态
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            const width = window.innerWidth;
            if (width > 768 && window.mobileMenuOpen) {
                window.mobileMenuOpen = false;
                const sidebar = document.getElementById('sidebar');
                const overlay = document.getElementById('sidebarOverlay');
                const menuButton = document.getElementById('mobileMenuButton');

                if (sidebar) sidebar.classList.remove('mobile-open');
                if (overlay) overlay.classList.remove('active');
                if (menuButton) {
                    menuButton.classList.remove('active');
                    menuButton.setAttribute('aria-label', '打开菜单');
                    menuButton.setAttribute('aria-expanded', 'false');
                }
                document.body.style.overflow = '';
            }
        }, 250);
    });

    console.log('✅ 基础组件初始化完成');
}

// ========== 调试函数 ==========
window.debugSystem = function() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');

    console.group('🔍 系统调试信息');
    console.log('全局变量:');
    console.log(`  sidebarCollapsed: ${window.sidebarCollapsed}`);
    console.log(`  mobileMenuOpen: ${window.mobileMenuOpen}`);
    console.log('DOM元素:');
    console.log(`  侧边栏: ${sidebar ? '存在' : '不存在'}`);
    console.log(`  主内容: ${mainContent ? '存在' : '不存在'}`);
    if (sidebar) {
        console.log(`  sidebar classes: ${sidebar.className}`);
    }
    if (mainContent) {
        console.log(`  mainContent classes: ${mainContent.className}`);
    }
    console.log(`  窗口宽度: ${window.innerWidth}px`);
    console.log(`  是否移动端: ${window.innerWidth <= 768}`);
    console.groupEnd();
};

// ========== 页面加载时初始化 ==========
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeBaseComponents);
} else {
    initializeBaseComponents();
}

console.log('💡 提示: 在控制台输入 debugSystem() 查看系统状态');
