// Global State
let trendData = [];
let selectedKeywords = {}; // { keyword: { velocity: 1.2, link: '' } }
let activeChartKeywords = [];

document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    checkApiStatus();
    initEventListeners();
    loadBlogHistory();
    
    // Set current date
    const dateBox = document.getElementById("current-date");
    if (dateBox) {
        dateBox.textContent = new Date().toISOString().split("T")[0];
    }
});

// 1. Tab Navigation Logic
function initTabs() {
    const navItems = document.querySelectorAll(".nav-item");
    const tabContents = document.querySelectorAll(".tab-content");
    const pageTitle = document.getElementById("page-title");
    const pageSubtitle = document.getElementById("page-subtitle");
    
    const tabMeta = {
        "trends-tab": {
            title: "식품 트렌드 분석 및 검증",
            subtitle: "네이버 쇼핑 데이터랩을 기반으로 검색 상승 속도(velocity)를 실시간 판별합니다."
        },
        "links-tab": {
            title: "브랜드커넥트 상품 매핑",
            subtitle: "확장 프로그램을 활용해 키워드와 매칭되는 상품 제휴 링크를 발급하고 입력합니다."
        },
        "blog-tab": {
            title: "AI 블로그 원고 작성기",
            subtitle: "선택된 트렌드 키워드와 제휴 링크를 조합해 표시광고법을 준수하는 포스팅 초안을 생성합니다."
        },
        "compliance-tab": {
            title: "네이버 브랜드커넥트 운영 가이드",
            subtitle: "공정위 지침 및 광고 심사 지침을 바탕으로 꼭 지켜야 할 주의 사항을 정리했습니다."
        }
    };

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetTab = item.getAttribute("data-tab");
            
            // Toggle active classes in nav
            navItems.forEach(nav => nav.classList.remove("active"));
            item.classList.add("active");
            
            // Toggle active classes in content
            tabContents.forEach(content => {
                content.classList.remove("active");
                if (content.id === targetTab) {
                    content.classList.add("active");
                }
            });
            
            // Update Title & Subtitle
            if (tabMeta[targetTab]) {
                pageTitle.textContent = tabMeta[targetTab].title;
                pageSubtitle.textContent = tabMeta[targetTab].subtitle;
            }
        });
    });
}

// 2. Load API credentials state from backend status
async function checkApiStatus() {
    try {
        const response = await fetch("/api/status");
        const data = await response.json();
        
        const naverDot = document.getElementById("naver-status-dot");
        const anthropicDot = document.getElementById("anthropic-status-dot");
        
        if (data.naver_configured) {
            naverDot.classList.add("connected");
        } else {
            naverDot.classList.remove("connected");
        }
        
        if (data.anthropic_configured) {
            anthropicDot.classList.add("connected");
        } else {
            anthropicDot.classList.remove("connected");
        }
    } catch (e) {
        console.error("Failed to check API status", e);
    }
}

// 3. Event Listeners Setup
function initEventListeners() {
    // Run Daily Trend Analysis
    document.getElementById("btn-run-analysis").addEventListener("click", runDailyAnalysis);
    
    // Add custom keywords
    document.getElementById("btn-add-custom").addEventListener("click", addCustomKeywords);
    
    // Go to Blog Tab
    document.getElementById("btn-go-to-blog").addEventListener("click", () => {
        const blogTabBtn = document.querySelector('[data-tab="blog-tab"]');
        if (blogTabBtn) blogTabBtn.click();
    });
    
    // Generate Blog Draft
    document.getElementById("btn-generate-blog").addEventListener("click", generateBlogDraft);
    
    // Copy Buttons
    document.getElementById("btn-copy-markdown").addEventListener("click", () => copyToClipboard("markdown"));
    document.getElementById("btn-copy-raw").addEventListener("click", () => copyToClipboard("raw"));
}

// 4. API Calls & Processing
async function runDailyAnalysis() {
    const loader = document.getElementById("trends-loader");
    const tableBody = document.getElementById("trends-table-body");
    
    loader.style.display = "inline-flex";
    tableBody.innerHTML = `<tr><td colspan="5" class="empty-table"><div class="spinner" style="margin: 0 auto 10px;"></div>분석 진행 중... 잠시만 기다려 주세요.</td></tr>`;
    
    try {
        const response = await fetch("/api/trends");
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "서버 오류가 발생했습니다.");
        }
        
        const data = await response.json();
        trendData = data;
        renderTrendsTable(trendData);
        
        // Auto select first 3 rising keywords to draw chart
        activeChartKeywords = data.slice(0, 3).map(d => d.keyword);
        drawTrendChart(trendData, activeChartKeywords);
    } catch (e) {
        tableBody.innerHTML = `<tr><td colspan="5" class="empty-table" style="color: var(--danger-color);">❌ 오류 발생: ${e.message}</td></tr>`;
    } finally {
        loader.style.display = "none";
    }
}

async function addCustomKeywords() {
    const input = document.getElementById("custom-keywords");
    const keywordsText = input.value.trim();
    if (!keywordsText) return;
    
    const keywords = keywordsText.split(",").map(k => k.trim()).filter(k => k);
    if (keywords.length === 0) return;
    
    const loader = document.getElementById("trends-loader");
    loader.style.display = "inline-flex";
    
    try {
        const response = await fetch("/api/trends/custom", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ keywords })
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "커스텀 키워드 검색 실패");
        }
        
        const customResults = await response.json();
        
        // Integrate into trendData
        customResults.forEach(item => {
            // Check if already exists, update or add
            const idx = trendData.findIndex(t => t.keyword === item.keyword);
            if (idx > -1) {
                trendData[idx] = { ...trendData[idx], ...item };
            } else {
                trendData.push({
                    keyword: item.keyword,
                    rising_score: 0,
                    appearances: 0,
                    new_entry: false,
                    datalab_velocity: item.datalab_velocity,
                    early_avg: item.early_avg,
                    late_avg: item.late_avg,
                    trend_series: item.trend_series
                });
            }
            
            // Add custom keyword to chart
            if (!activeChartKeywords.includes(item.keyword)) {
                activeChartKeywords.push(item.keyword);
            }
        });
        
        // Sort and re-render
        trendData.sort((a, b) => b.datalab_velocity - a.datalab_velocity);
        renderTrendsTable(trendData);
        drawTrendChart(trendData, activeChartKeywords);
        input.value = "";
    } catch (e) {
        alert("키워드 분석 중 오류가 발생했습니다: " + e.message);
    } finally {
        loader.style.display = "none";
    }
}

// 5. Render list and mapper components
function renderTrendsTable(data) {
    const tableBody = document.getElementById("trends-table-body");
    tableBody.innerHTML = "";
    
    if (data.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="5" class="empty-table">데이터가 없습니다.</td></tr>`;
        return;
    }
    
    data.forEach(item => {
        const row = document.createElement("tr");
        
        const velBadgeClass = item.datalab_velocity >= 1.1 ? "badge-rising" : "badge-stable";
        const newBadge = item.new_entry ? `<span class="badge badge-new">NEW</span>` : "";
        const isAdded = selectedKeywords[item.keyword] !== undefined;
        
        const actionBtn = isAdded 
            ? `<button class="btn btn-secondary btn-sm" onclick="removeKeyword('${item.keyword}')" title="클릭 시 선택 해제">✓ 선택됨</button>`
            : `<button class="btn btn-primary btn-sm" onclick="addKeyword('${item.keyword}', ${item.datalab_velocity})">선택</button>`;
            
        row.innerHTML = `
            <td>
                <span class="keyword-select-toggle" style="cursor:pointer; font-weight:600;" onclick="toggleChartKeyword('${item.keyword}')">
                    ${item.keyword}
                </span>
            </td>
            <td>
                <span class="badge ${velBadgeClass}">${item.datalab_velocity}x</span>
            </td>
            <td>${item.rising_score}</td>
            <td>${newBadge}</td>
            <td>${actionBtn}</td>
        `;
        tableBody.appendChild(row);
    });
}

function addKeyword(keyword, velocity) {
    if (!selectedKeywords[keyword]) {
        selectedKeywords[keyword] = { velocity, link: "" };
        
        // Auto-copy keyword to clipboard for easy search in Chrome extension
        navigator.clipboard.writeText(keyword).then(() => {
            showNotification(`"${keyword}" 키워드가 선택 및 복사되었습니다!`);
        }).catch(err => {
            console.error("Auto-copy failed", err);
            showNotification(`"${keyword}" 키워드가 선택되었습니다.`);
        });
        
        renderMapperList();
        renderTrendsTable(trendData);
    }
}

function removeKeyword(keyword) {
    if (selectedKeywords[keyword]) {
        delete selectedKeywords[keyword];
        renderMapperList();
        renderTrendsTable(trendData);
    }
}

function toggleChartKeyword(keyword) {
    const idx = activeChartKeywords.indexOf(keyword);
    if (idx > -1) {
        activeChartKeywords.splice(idx, 1);
    } else {
        activeChartKeywords.push(keyword);
    }
    drawTrendChart(trendData, activeChartKeywords);
}

// 6. Draw offline SVG Trend Chart
function drawTrendChart(data, keywords) {
    const svg = document.getElementById("trend-svg-chart");
    const legendBox = document.getElementById("chart-legend-box");
    
    // Clear old lines and legends
    svg.querySelectorAll(".chart-line, .chart-marker").forEach(el => el.remove());
    legendBox.innerHTML = "";
    
    if (keywords.length === 0) {
        document.getElementById("chart-placeholder").style.display = "block";
        return;
    }
    document.getElementById("chart-placeholder").style.display = "none";
    
    const colors = ["#03c75a", "#3867d6", "#eb4d4b", "#f9ca24", "#9b59b6", "#e67e22"];
    
    // Extract series and merge boundaries
    let maxVal = 1.0;
    let dates = [];
    
    const datasets = keywords.map((kw, idx) => {
        const item = data.find(d => d.keyword === kw);
        const series = item ? item.trend_series : [];
        series.forEach(pt => {
            if (pt.ratio > maxVal) maxVal = pt.ratio;
            if (!dates.includes(pt.period)) dates.push(pt.period);
        });
        return {
            keyword: kw,
            color: colors[idx % colors.length],
            points: series.map(pt => ({ x: pt.period, y: pt.ratio }))
        };
    }).filter(d => d.points.length > 0);
    
    if (datasets.length === 0) {
        document.getElementById("chart-placeholder").style.display = "block";
        return;
    }
    
    dates.sort();
    
    // Dimensions
    const paddingLeft = 50;
    const paddingRight = 20;
    const paddingTop = 20;
    const paddingBottom = 55;
    const width = 600;
    const height = 240;
    
    const graphWidth = width - paddingLeft - paddingRight;
    const graphHeight = height - paddingTop - paddingBottom;
    
    // Draw grid dates labels
    svg.querySelectorAll(".date-label").forEach(el => el.remove());
    if (dates.length > 1) {
        const interval = Math.max(1, Math.floor(dates.length / 5));
        for (let i = 0; i < dates.length; i += interval) {
            const x = paddingLeft + (i / (dates.length - 1)) * graphWidth;
            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.setAttribute("x", x);
            text.setAttribute("y", height - 20);
            text.setAttribute("text-anchor", "middle");
            text.setAttribute("class", "chart-text date-label");
            text.setAttribute("fill", "#889");
            text.textContent = dates[i].substring(5); // MM-DD
            svg.appendChild(text);
        }
    }
    
    // Draw Lines
    datasets.forEach(dataset => {
        let pathPoints = [];
        
        dataset.points.forEach(pt => {
            const dateIdx = dates.indexOf(pt.x);
            if (dateIdx === -1) return;
            
            const px = paddingLeft + (dateIdx / (dates.length - 1)) * graphWidth;
            const py = paddingTop + graphHeight - (pt.y / maxVal) * graphHeight;
            pathPoints.push(`${px},${py}`);
        });
        
        if (pathPoints.length > 0) {
            // Draw Path Line
            const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
            polyline.setAttribute("points", pathPoints.join(" "));
            polyline.setAttribute("fill", "none");
            polyline.setAttribute("stroke", dataset.color);
            polyline.setAttribute("stroke-width", "2.5");
            polyline.setAttribute("class", "chart-line");
            svg.appendChild(polyline);
            
            // Draw last point dot
            const lastPtStr = pathPoints[pathPoints.length - 1].split(",");
            const lastX = parseFloat(lastPtStr[0]);
            const lastY = parseFloat(lastPtStr[1]);
            
            const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            circle.setAttribute("cx", lastX);
            circle.setAttribute("cy", lastY);
            circle.setAttribute("r", "4.5");
            circle.setAttribute("fill", dataset.color);
            circle.setAttribute("class", "chart-marker");
            svg.appendChild(circle);
        }
        
        // Draw Legend item
        const legendItem = document.createElement("div");
        legendItem.className = "legend-item";
        legendItem.innerHTML = `
            <span class="legend-color" style="background-color: ${dataset.color};"></span>
            <span>${dataset.keyword}</span>
        `;
        legendItem.addEventListener("click", () => toggleChartKeyword(dataset.keyword));
        legendBox.appendChild(legendItem);
    });
    
    // Update axis text maximum
    const yAxisLabel = svg.querySelector("text[x='15'][y='25']");
    if (yAxisLabel) yAxisLabel.textContent = Math.round(maxVal);
    const yAxisMidLabel = svg.querySelector("text[x='15'][y='105']");
    if (yAxisMidLabel) yAxisMidLabel.textContent = Math.round(maxVal / 2);
}

// 7. Render Brand Connect mapping inputs
function renderMapperList() {
    const listContainer = document.getElementById("mapper-keywords-list");
    const summaryList = document.getElementById("mapped-links-summary");
    const btnGoToBlog = document.getElementById("btn-go-to-blog");
    const btnGenerateBlog = document.getElementById("btn-generate-blog");
    
    listContainer.innerHTML = "";
    summaryList.innerHTML = "";
    
    const keys = Object.keys(selectedKeywords);
    if (keys.length === 0) {
        listContainer.innerHTML = `<div class="empty-mapper">선택된 키워드가 없습니다. 트렌드 분석기 탭에서 키워드를 추가해 주세요.</div>`;
        summaryList.innerHTML = `<li class="summary-empty">등록된 링크가 없습니다.</li>`;
        btnGoToBlog.disabled = true;
        btnGenerateBlog.disabled = true;
        return;
    }
    
    btnGoToBlog.disabled = false;
    btnGenerateBlog.disabled = false;
    
    const creatorId = document.getElementById("creator-id-input").value.trim() || "971564859961248";
    const brandConnectUrl = `https://brandconnect.naver.com/${creatorId}/affiliate/products`;
    
    keys.forEach(kw => {
        const item = selectedKeywords[kw];
        
        // Create mapping row
        const row = document.createElement("div");
        row.className = "mapper-row";
        row.innerHTML = `
            <div class="mapper-info">
                <h4>${kw}</h4>
                <div class="kw-meta">Velocity: ${item.velocity}x</div>
            </div>
            <div class="mapper-actions-local">
                <button class="btn btn-secondary btn-sm" onclick="copyTextToClipboard('${kw}')">🔑 복사</button>
            </div>
            <div class="mapper-input">
                <input type="text" placeholder="네이버 브랜드커넥트 상품 링크 붙여넣기" value="${item.link}" oninput="updateLinkMapping('${kw}', this.value)">
            </div>
            <div>
                <a class="btn btn-secondary btn-sm" href="${brandConnectUrl}" target="_blank">검색화면 열기 ↗</a>
            </div>
        `;
        listContainer.appendChild(row);
        
        // Create sidebar summary item
        const summaryItem = document.createElement("li");
        const linkStatus = item.link.trim() ? "🟢 연결됨" : "🔴 미연결";
        summaryItem.innerHTML = `
            <span>${kw}</span>
            <strong>${linkStatus}</strong>
        `;
        summaryList.appendChild(summaryItem);
    });
}

function updateLinkMapping(keyword, value) {
    if (selectedKeywords[keyword]) {
        selectedKeywords[keyword].link = value.trim();
        // Update summaries without redrawing full list to avoid focus loss
        renderSummaryList();
    }
}

function renderSummaryList() {
    const summaryList = document.getElementById("mapped-links-summary");
    summaryList.innerHTML = "";
    
    Object.keys(selectedKeywords).forEach(kw => {
        const item = selectedKeywords[kw];
        const summaryItem = document.createElement("li");
        const linkStatus = item.link.trim() ? "🟢 연결됨" : "🔴 미연결";
        summaryItem.innerHTML = `
            <span>${kw}</span>
            <strong>${linkStatus}</strong>
        `;
        summaryList.appendChild(summaryItem);
    });
}

async function copyTextToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        // Show temporary visual feedback
        alert(`"${text}" 키워드가 클립보드에 복사되었습니다. 확장 프로그램에서 붙여넣어 주세요.`);
    } catch (err) {
        console.error("Clipboard copy failed", err);
    }
}

// 8. AI Blog Post generation call
async function generateBlogDraft() {
    const loader = document.getElementById("blog-loader");
    const previewContainer = document.getElementById("markdown-preview");
    
    const keywords_with_links = Object.keys(selectedKeywords).map(kw => ({
        keyword: kw,
        link: selectedKeywords[kw].link
    }));
    
    if (keywords_with_links.length === 0) {
        alert("선택된 키워드가 없습니다.");
        return;
    }
    
    loader.style.display = "inline-flex";
    previewContainer.innerHTML = `
        <div class="preview-placeholder">
            <div class="spinner" style="margin-bottom:12px;"></div>
            <p>Claude AI 작가가 포스팅 원고를 성심성의껏 작성하는 중입니다... (15~30초 소요)</p>
        </div>
    `;
    
    const titleHint = document.getElementById("blog-title-input").value.trim() || null;
    const model = document.getElementById("ai-model-select").value;
    
    try {
        const response = await fetch("/api/generate-blog", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                title_hint: titleHint,
                keywords_with_links,
                model
            })
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "블로그 원고 생성 실패");
        }
        
        const data = await response.json();
        
        // Save raw content text
        window.generatedPostMarkdown = data.blog_post_markdown;
        
        // Display in rich text HTML
        renderMarkdownHTML(data.blog_post_markdown);
        
        // Perform compliance diagnostics
        diagnoseCompliance(data.blog_post_markdown, data.compliance);

        // Reload DB History list
        loadBlogHistory();
    } catch (e) {
        previewContainer.innerHTML = `
            <div class="preview-placeholder" style="color: var(--danger-color);">
                <span>❌ 에러가 발생했습니다.</span>
                <p>${e.message}</p>
            </div>
        `;
    } finally {
        loader.style.display = "none";
    }
}

// Simple dynamic regex-based markdown viewer
function renderMarkdownHTML(md) {
    const previewContainer = document.getElementById("markdown-preview");
    
    let html = md
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
        
    // Headers H1-H4
    html = html.replace(/^# (.*?)$/gm, "<h1>$1</h1>");
    html = html.replace(/^## (.*?)$/gm, "<h2>$1</h2>");
    html = html.replace(/^### (.*?)$/gm, "<h3>$1</h3>");
    html = html.replace(/^#### (.*?)$/gm, "<h4>$1</h4>");
    
    // Blockquotes
    html = html.replace(/^&gt;\s?(.*?)$/gm, "<blockquote><p>$1</p></blockquote>");
    // Merge adjacent blockquotes
    html = html.replace(/<\/blockquote>\s*<blockquote>/g, "<br>");
    
    // Bold styles
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    
    // Links [Text](URL)
    html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // Lists
    html = html.replace(/^\-\s?(.*?)$/gm, "<li>$1</li>");
    // Wrap lists (simplified)
    html = html.replace(/(<li>.*?<\/li>)/gs, "<ul>$1</ul>");
    
    // Replace linebreaks with p tags
    html = html.split(/\n\n+/).map(para => {
        if (para.startsWith("<h") || para.startsWith("<blockquote") || para.startsWith("<ul")) {
            return para;
        }
        return `<p>${para.replace(/\n/g, "<br>")}</p>`;
    }).join("");
    
    previewContainer.innerHTML = html;
}

// 9. Compliance Diagnostics UI Updates
function diagnoseCompliance(markdownText, complianceData) {
    const chkDisclosure = document.getElementById("chk-disclosure");
    const chkAdvertising = document.getElementById("chk-advertising");
    const chkDuration = document.getElementById("chk-duration");
    
    // 1. Disclosure text check
    if (complianceData.has_disclosure) {
        chkDisclosure.className = "check-item pass";
        chkDisclosure.querySelector(".check-icon").textContent = "✓";
    } else {
        chkDisclosure.className = "check-item warning";
        chkDisclosure.querySelector(".check-icon").textContent = "⚠️";
    }
    
    // 2. Advertising Guidelines
    chkAdvertising.className = "check-item pass";
    chkAdvertising.querySelector(".check-icon").textContent = "✓";
    
    // 3. Post Duration
    chkDuration.className = "check-item pass";
    chkDuration.querySelector(".check-icon").textContent = "✓";
}

// 10. Copy Utilities
async function copyToClipboard(mode) {
    const markdownText = window.generatedPostMarkdown;
    if (!markdownText) {
        alert("복사할 원고 내용이 없습니다. 먼저 원고를 생성해 주세요.");
        return;
    }
    
    let textToCopy = markdownText;
    if (mode === "raw") {
        // Strip basic markdown tags
        textToCopy = markdownText
            .replace(/[#*`>_\-]/g, "")
            .replace(/\[(.*?)\]\(.*?\)/g, "$1");
    }
    
    try {
        await navigator.clipboard.writeText(textToCopy);
        alert("원고가 클립보드에 성공적으로 복사되었습니다. 네이버 블로그 스마트에디터에 붙여넣어 주세요.");
    } catch (err) {
        alert("클립보드 복사 중 실패가 발생했습니다: " + err.message);
    }
}

// 11. Database Blog History UI loading
async function loadBlogHistory() {
    const listContainer = document.getElementById("blog-history-list");
    if (!listContainer) return;
    
    try {
        const response = await fetch("/api/history");
        if (!response.ok) throw new Error("히스토리 데이터 로드 실패");
        const historyData = await response.json();
        
        listContainer.innerHTML = "";
        
        if (historyData.length === 0) {
            listContainer.innerHTML = `<li class="history-empty">작성된 블로그 히스토리가 없습니다.</li>`;
            return;
        }
        
        // Cache history data globally
        window.blogHistoryCache = historyData;
        
        historyData.forEach((item, index) => {
            const formattedDate = item.created_at ? item.created_at.replace("T", " ").substring(0, 16) : "";
            const li = document.createElement("li");
            li.className = "history-item";
            li.innerHTML = `
                <div class="history-item-title">${item.title || "요즘 뜨는 식품 트렌드"}</div>
                <div class="history-item-date">📅 ${formattedDate} (${item.keywords.join(", ")})</div>
            `;
            li.addEventListener("click", () => loadHistoryItem(index));
            listContainer.appendChild(li);
        });
    } catch (e) {
        console.error(e);
        listContainer.innerHTML = `<li class="history-empty" style="color: var(--danger-color);">DB 연결 대기 중...</li>`;
    }
}

function loadHistoryItem(index) {
    const historyData = window.blogHistoryCache;
    if (!historyData || !historyData[index]) return;
    
    const item = historyData[index];
    
    // Save to global generated post markdown state
    window.generatedPostMarkdown = item.content;
    
    // Render draft
    renderMarkdownHTML(item.content);
    
    // Run diagnostics
    const disclosureText = "이 포스팅은 네이버 쇼핑 커넥트 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.";
    const hasDisclosure = item.content.includes(disclosureText);
    
    diagnoseCompliance(item.content, {
        has_disclosure: hasDisclosure,
        disclosure_text: disclosureText,
        advertising_policy_warning: true,
        post_duration_warning: true,
        penalty_system_warning: true
    });
    
    alert(`"${item.title || "식품 트렌드"}" 과거 원고 초안을 불러왔습니다.`);
}

// 12. Toast Notification Helper
function showNotification(message) {
    const toast = document.createElement("div");
    toast.style.position = "fixed";
    toast.style.top = "20px";
    toast.style.right = "20px";
    toast.style.backgroundColor = "var(--primary-color)"; // Naver Green
    toast.style.color = "white";
    toast.style.padding = "12px 20px";
    toast.style.borderRadius = "var(--border-radius-md)";
    toast.style.boxShadow = "0 4px 12px rgba(3, 199, 90, 0.3)";
    toast.style.zIndex = "9999";
    toast.style.fontFamily = "'Noto Sans KR', sans-serif";
    toast.style.fontSize = "13px";
    toast.style.fontWeight = "600";
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.3s ease, transform 0.3s ease";
    toast.style.transform = "translateY(-10px)";
    toast.innerText = message;
    
    document.body.appendChild(toast);
    
    // Trigger animation
    setTimeout(() => {
        toast.style.opacity = "1";
        toast.style.transform = "translateY(0)";
    }, 50);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(-10px)";
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}
