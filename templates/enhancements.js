/**
 * 前端增强脚本
 * 提供Toast通知、按钮反馈和交互优化
 */

(function() {
    'use strict';

    // ==================== Toast 通知系统 ====================

    const Toast = {
        container: null,
        init: function() {
            // 创建Toast容器
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        },

        show: function(message, type = 'info', options = {}) {
            if (!this.container) {
                this.init();
            }

            const {
                title = '',
                duration = type === 'error' ? 5000 : 3000,
                closeable = true,
                icon = this.getDefaultIcon(type)
            } = options;

            const toast = document.createElement('div');
            toast.className = `toast ${type}`;

            toast.innerHTML = `
                <div class="toast-icon">${icon}</div>
                <div class="toast-content">
                    ${title ? `<div class="toast-title">${title}</div>` : ''}
                    <div class="toast-message">${message}</div>
                </div>
                ${closeable ? '<button class="toast-close" onclick="this.parentElement.remove()">×</button>' : ''}
            `;

            this.container.appendChild(toast);

            // 自动移除
            if (duration > 0) {
                setTimeout(() => {
                    toast.classList.add('removing');
                    setTimeout(() => toast.remove(), 300);
                }, duration);
            }

            return toast;
        },

        success: function(message, options = {}) {
            return this.show(message, 'success', options);
        },

        error: function(message, options = {}) {
            return this.show(message, 'error', options);
        },

        warning: function(message, options = {}) {
            return this.show(message, 'warning', options);
        },

        info: function(message, options = {}) {
            return this.show(message, 'info', options);
        },

        getDefaultIcon: function(type) {
            const icons = {
                success: '✅',
                error: '❌',
                warning: '⚠️',
                info: 'ℹ️'
            };
            return icons[type] || icons.info;
        }
    };

    // 导出到全局
    window.Toast = Toast;

    // ==================== 按钮增强 ====================

    function enhanceButtons() {
        // 为所有按钮添加点击反馈
        document.querySelectorAll('.btn, .btn-secondary, .btn-icon').forEach(button => {
            // 防止重复绑定
            if (button.dataset.enhanced) return;
            button.dataset.enhanced = 'true';

            // 点击效果
            button.addEventListener('click', function() {
                this.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 150);
            });

            // 键盘支持
            button.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.click();
                }
            });
        });
    }

    // ==================== 表单验证增强 ====================

    function enhanceFormValidation() {
        const form = document.getElementById('searchForm');
        if (!form) return;

        const inputs = form.querySelectorAll('input[required], select[required]');

        inputs.forEach(input => {
            // 实时验证
            input.addEventListener('blur', function() {
                validateField(this);
            });

            input.addEventListener('input', function() {
                if (this.classList.contains('error')) {
                    validateField(this);
                }
            });
        });
    }

    function validateField(field) {
        const value = field.value.trim();

        if (field.hasAttribute('required') && !value) {
            field.classList.add('error');
            field.classList.remove('success');
            return false;
        }

        field.classList.remove('error');
        field.classList.add('success');
        return true;
    }

    // ==================== 加载状态管理 ====================

    function setLoading(button, loading) {
        if (!button) return;

        if (loading) {
            button.classList.add('loading');
            button.disabled = true;
            button.dataset.originalText = button.textContent;
        } else {
            button.classList.remove('loading');
            button.disabled = false;
            if (button.dataset.originalText) {
                button.textContent = button.dataset.originalText;
            }
        }
    }

    // 导出到全局
    window.setLoading = setLoading;

    // ==================== 进度条 ====================

    function showProgress(container) {
        const progressBar = document.createElement('div');
        progressBar.className = 'progress-bar';
        progressBar.innerHTML = '<div class="progress-bar-fill"></div>';

        if (typeof container === 'string') {
            container = document.querySelector(container);
        }

        if (container) {
            container.appendChild(progressBar);
        }

        return {
            element: progressBar,
            update: function(percent) {
                const fill = progressBar.querySelector('.progress-bar-fill');
                if (fill) {
                    fill.style.width = percent + '%';
                }
            },
            complete: function() {
                const fill = progressBar.querySelector('.progress-bar-fill');
                if (fill) {
                    fill.style.width = '100%';
                }
                setTimeout(() => progressBar.remove(), 500);
            },
            remove: function() {
                progressBar.remove();
            }
        };
    }

    window.showProgress = showProgress;

    // ==================== 结果选择增强 ====================

    function enhanceResultSelection() {
        const resultsContainer = document.getElementById('results');
        if (!resultsContainer) return;

        // 使用事件委托处理结果项点击
        resultsContainer.addEventListener('click', function(e) {
            const resultItem = e.target.closest('.result-item');
            if (!resultItem) return;

            // 切换选中状态
            resultItem.classList.toggle('selected');

            // 更新选中计数
            updateSelectionCount();
        });
    }

    function updateSelectionCount() {
        const selected = document.querySelectorAll('.result-item.selected').length;
        const countElement = document.getElementById('selectedCount');

        if (countElement) {
            countElement.textContent = selected;
        }
    }

    // ==================== 快捷键支持 ====================

    function initKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + K: 聚焦搜索框
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.getElementById('subject');
                if (searchInput) {
                    searchInput.focus();
                }
            }

            // Esc: 关闭模态框
            if (e.key === 'Escape') {
                const modals = document.querySelectorAll('.modal[style*="display: block"]');
                modals.forEach(modal => {
                    modal.style.display = 'none';
                });
            }

            // Ctrl/Cmd + Enter: 提交搜索
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                const searchForm = document.getElementById('searchForm');
                const searchBtn = document.getElementById('searchBtn');
                if (searchForm && searchBtn && !searchBtn.disabled) {
                    e.preventDefault();
                    searchBtn.click();
                }
            }
        });
    }

    // ==================== 错误处理增强 ====================

    function handleApiError(error, context = '') {
        console.error('[API Error]', context, error);

        let message = '操作失败，请重试';

        if (error.message) {
            message = error.message;
        } else if (typeof error === 'string') {
            message = error;
        }

        Toast.error(message, {
            title: context || '错误',
            duration: 5000
        });
    }

    window.handleApiError = handleApiError;

    // ==================== 性能监控 ====================

    function trackPerformance(metricName, value) {
        if (window.performance && window.performance.mark) {
            const markName = `metric_${metricName}`;
            performance.mark(markName);

            if (value !== undefined) {
                console.log(`[Performance] ${metricName}: ${value}ms`);
            }
        }
    }

    window.trackPerformance = trackPerformance;

    // ==================== 初始化 ====================

    function init() {
        console.log('[Enhancements] 初始化前端增强...');

        // 等待DOM加载完成
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initEnhancements);
        } else {
            initEnhancements();
        }
    }

    function initEnhancements() {
        enhanceButtons();
        enhanceFormValidation();
        enhanceResultSelection();
        initKeyboardShortcuts();

        // 监听动态添加的按钮
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length) {
                    enhanceButtons();
                }
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        console.log('[Enhancements] 前端增强初始化完成');
    }

    // 启动
    init();

})();
