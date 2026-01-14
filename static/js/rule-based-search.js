/**
 * 规则搜索引擎 - 前端集成代码
 *
 * 使用方法：
 * 1. 将此文件复制到 static/js/ 目录
 * 2. 在 templates/index.html 中引用：
 *    <script src="/static/js/rule-based-search.js"></script>
 * 3. 添加UI元素（见下方HTML示例）
 */

// ============================================================================
// 规则搜索API调用
// ============================================================================

/**
 * 执行规则搜索
 * @param {string} country - 国家代码 (ID, SA, US等)
 * @param {string} grade - 年级 (1, 2, 3...)
 * @param {string} subject - 学科 (math, science等)
 * @param {number} maxResults - 最大结果数（可选）
 * @returns {Promise<Object>} 搜索结果
 */
async function searchWithRuleBased(country, grade, subject, maxResults = 20) {
    const API_URL = '/api/search/rule-based';
    const API_KEY = localStorage.getItem('apiKey') || 'dev-key-123';

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_KEY
            },
            body: JSON.stringify({
                country: country,
                grade: grade,
                subject: subject,
                max_results: maxResults
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || '搜索失败');
        }

        return data;

    } catch (error) {
        console.error('规则搜索失败:', error);
        throw error;
    }
}

/**
 * 获取规则搜索配置
 * @returns {Promise<Object>} 配置信息
 */
async function getRuleBasedConfig() {
    const API_URL = '/api/search/rule-based/config';
    const API_KEY = localStorage.getItem('apiKey') || 'dev-key-123';

    try {
        const response = await fetch(API_URL, {
            method: 'GET',
            headers: {
                'X-API-Key': API_KEY
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || '获取配置失败');
        }

        return data;

    } catch (error) {
        console.error('获取配置失败:', error);
        throw error;
    }
}

// ============================================================================
// UI组件和交互
// ============================================================================

/**
 * 显示规则搜索结果
 * @param {Object} data - API响应数据
 */
function displayRuleBasedResults(data) {
    const container = document.getElementById('search-results');

    if (!data.success) {
        container.innerHTML = `
            <div class="error-message">
                <p>❌ ${data.message}</p>
            </div>
        `;
        return;
    }

    if (!data.results || data.results.length === 0) {
        container.innerHTML = `
            <div class="no-results">
                <p>🔍 没有找到结果</p>
                <p>请尝试其他搜索条件</p>
            </div>
        `;
        return;
    }

    // 显示本地化信息
    displayLocalizedInfo(data.localized_info, data.search_metadata);

    // 显示结果列表
    let resultsHTML = '<div class="results-list">';

    data.results.forEach((result, index) => {
        resultsHTML += `
            <div class="result-item" data-score="${result.score}">
                <div class="result-header">
                    <span class="result-score">${result.score.toFixed(1)}分</span>
                    <span class="result-source">${result.score_reason}</span>
                </div>
                <h3 class="result-title">
                    <a href="${result.url}" target="_blank" rel="noopener">
                        ${result.title}
                    </a>
                </h3>
                <p class="result-snippet">${result.snippet || '暂无描述'}</p>
                <p class="result-url">${result.url}</p>
            </div>
        `;
    });

    resultsHTML += '</div>';

    container.innerHTML = resultsHTML;

    // 显示统计信息
    const statsHTML = `
        <div class="search-stats">
            <p>✅ 找到 <strong>${data.results.length}</strong> 个结果</p>
            <p>⭐ 最高分: <strong>${data.search_metadata.top_score.toFixed(1)}</strong></p>
            <p>🎯 使用查询: <strong>${data.search_metadata.queries_used.length}</strong> 个</p>
        </div>
    `;

    document.getElementById('search-stats').innerHTML = statsHTML;
}

/**
 * 显示本地化信息
 * @param {Object} localizedInfo - 本地化信息
 * @param {Object} metadata - 搜索元数据
 */
function displayLocalizedInfo(localizedInfo, metadata) {
    const container = document.getElementById('localized-info');

    if (!container) return;

    const html = `
        <div class="localized-info-card">
            <h3>📍 搜索信息</h3>
            <div class="info-grid">
                <div class="info-item">
                    <span class="label">国家:</span>
                    <span class="value">${localizedInfo.country}</span>
                </div>
                <div class="info-item">
                    <span class="label">年级:</span>
                    <span class="value">${localizedInfo.grade}</span>
                </div>
                <div class="info-item">
                    <span class="label">学科:</span>
                    <span class="value">${localizedInfo.subject}</span>
                </div>
                <div class="info-item">
                    <span class="label">课程:</span>
                    <span class="value">${localizedInfo.curriculum}</span>
                </div>
                <div class="info-item">
                    <span class="label">状态:</span>
                    <span class="value ${localizedInfo.supported ? 'supported' : 'unsupported'}">
                        ${localizedInfo.supported ? '✅ 支持' : '❌ 不支持'}
                    </span>
                </div>
            </div>
            <div class="queries-section">
                <h4>使用的查询:</h4>
                <ul>
                    ${metadata.queries_used.map(q => `<li>${q}</li>`).join('')}
                </ul>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

/**
 * 显示加载状态
 */
function showLoading() {
    const container = document.getElementById('search-results');
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>正在搜索...</p>
        </div>
    `;
}

/**
 * 显示错误信息
 * @param {string} message - 错误消息
 */
function showError(message) {
    const container = document.getElementById('search-results');
    container.innerHTML = `
        <div class="error-message">
            <p>❌ ${message}</p>
        </div>
    `;
}

// ============================================================================
// 搜索模式选择器
// ============================================================================

/**
 * 初始化搜索模式选择器
 */
function initSearchModeSelector() {
    const selector = document.getElementById('search-mode-selector');
    if (!selector) return;

    selector.addEventListener('change', (e) => {
        const mode = e.target.value;
        localStorage.setItem('searchMode', mode);
        console.log('搜索模式已切换到:', mode);
    });

    // 恢复上次选择的模式
    const savedMode = localStorage.getItem('searchMode') || 'ai';
    const radioButton = selector.querySelector(`input[value="${savedMode}"]`);
    if (radioButton) {
        radioButton.checked = true;
    }
}

/**
 * 获取当前搜索模式
 * @returns {string} 搜索模式 ('ai' 或 'rule_based')
 */
function getSearchMode() {
    const selector = document.getElementById('search-mode-selector');
    if (!selector) return 'ai';

    const selected = selector.querySelector('input:checked');
    return selected ? selected.value : 'ai';
}

// ============================================================================
// 主搜索函数（集成到现有搜索表单）
// ============================================================================

/**
 * 执行搜索（自动选择AI或规则搜索）
 * @param {Event} event - 表单提交事件
 */
async function executeSearch(event) {
    event.preventDefault();

    const country = document.getElementById('country-select').value;
    const grade = document.getElementById('grade-select').value;
    const subject = document.getElementById('subject-select').value;
    const searchMode = getSearchMode();

    console.log(`执行${searchMode === 'rule_based' ? '规则' : 'AI'}搜索:`, {country, grade, subject});

    showLoading();

    try {
        let result;

        if (searchMode === 'rule_based') {
            // 使用规则搜索
            result = await searchWithRuleBased(country, grade, subject);
        } else {
            // 使用现有AI搜索
            result = await executeExistingSearch(country, grade, subject);
        }

        displayRuleBasedResults(result);

    } catch (error) {
        showError(error.message);
    }
}

// ============================================================================
// 页面加载时初始化
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // 初始化搜索模式选择器
    initSearchModeSelector();

    // 加载配置并填充国家选项
    loadRuleBasedConfig();

    console.log('✅ 规则搜索引擎前端已加载');
});

/**
 * 加载规则搜索配置
 */
async function loadRuleBasedConfig() {
    try {
        const config = await getRuleBasedConfig();

        if (config.success) {
            console.log('支持的国家:', config.supported_countries);
            console.log('国家详情:', config.country_details);

            // 可以在这里更新国家选择器
            updateCountrySelector(config.supported_countries);
        }

    } catch (error) {
        console.warn('加载规则搜索配置失败:', error);
    }
}

/**
 * 更新国家选择器
 * @param {Array} countries - 支持的国家列表
 */
function updateCountrySelector(countries) {
    const selector = document.getElementById('country-select');
    if (!selector) return;

    // 标记支持规则搜索的国家
    Array.from(selector.options).forEach(option => {
        if (countries.includes(option.value)) {
            option.label = `${option.label} (支持规则搜索) ⚡`;
        }
    });
}

// ============================================================================
// CSS样式（复制到你的CSS文件或style标签中）
// ============================================================================

const ruleBasedSearchCSS = `
/* 规则搜索特定样式 */
.localized-info-card {
    background: #f0f9ff;
    border: 1px solid #0ea5e9;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}

.localized-info-card h3 {
    margin-top: 0;
    color: #0369a1;
}

.info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 10px;
    margin: 15px 0;
}

.info-item {
    display: flex;
    justify-content: space-between;
    padding: 5px 0;
}

.info-item .label {
    font-weight: 600;
    color: #64748b;
}

.info-item .value.supported {
    color: #16a34a;
    font-weight: 600;
}

.info-item .value.unsupported {
    color: #dc2626;
}

.queries-section h4 {
    margin-bottom: 10px;
    color: #0369a1;
}

.queries-section ul {
    list-style: none;
    padding-left: 0;
}

.queries-section li {
    background: white;
    padding: 8px 12px;
    margin: 5px 0;
    border-radius: 4px;
    border-left: 3px solid #0ea5e9;
    font-family: monospace;
}

.result-item {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
    background: white;
    transition: box-shadow 0.2s;
}

.result-item:hover {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.result-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
}

.result-score {
    font-weight: 700;
    color: #16a34a;
    font-size: 1.1em;
}

.result-source {
    color: #64748b;
    font-size: 0.9em;
}

.result-title {
    margin: 8px 0;
}

.result-title a {
    color: #0ea5e9;
    text-decoration: none;
}

.result-title a:hover {
    text-decoration: underline;
}

.result-snippet {
    color: #475569;
    margin: 8px 0;
}

.result-url {
    color: #94a3b8;
    font-size: 0.9em;
    margin: 0;
}

.search-mode-selector {
    margin: 20px 0;
    padding: 15px;
    background: #fef3c7;
    border: 1px solid #f59e0b;
    border-radius: 8px;
}

.search-mode-selector label {
    margin-right: 20px;
    font-weight: 500;
}

.loading {
    text-align: center;
    padding: 40px;
}

.spinner {
    border: 4px solid #f3f4f6;
    border-top: 4px solid #0ea5e9;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
    margin: 0 auto 20px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
`;

// 导出CSS（如果需要）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ruleBasedSearchCSS };
}
