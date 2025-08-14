// NextGen Hub Dashboard JavaScript

// Language Manager
class LanguageManager {
    constructor() {
        this.currentLanguage = localStorage.getItem('language') || 'ar';
        this.translations = {
            ar: {
                app_title: 'NextGen Hub',
                subtitle: 'لوحة المراقبة المتقدمة',
                system_connected: 'النظام متصل',
                last_update: 'آخر تحديث',
                now: 'الآن',
                overview: 'نظرة عامة',
                projects: 'المشاريع',
                monitoring: 'المراقبة',
                logs: 'السجلات',
                settings: 'الإعدادات',
                total_projects: 'إجمالي المشاريع',
                running_projects: 'المشاريع النشطة',
                stopped_projects: 'المشاريع المتوقفة',
                system_uptime: 'وقت تشغيل النظام',
                add_project: 'إضافة مشروع',
                project_name: 'اسم المشروع',
                working_directory: 'مجلد العمل',
                command: 'الأمر',
                arguments: 'المعاملات',
                log_path: 'مسار السجل',
                start: 'تشغيل',
                stop: 'إيقاف',
                restart: 'إعادة تشغيل',
                edit: 'تعديل',
                delete: 'حذف',
                running: 'يعمل',
                stopped: 'متوقف',
                error: 'خطأ'
            },
            en: {
                app_title: 'NextGen Hub',
                subtitle: 'Advanced Monitoring Dashboard',
                system_connected: 'System Connected',
                last_update: 'Last Update',
                now: 'Now',
                overview: 'Overview',
                projects: 'Projects',
                monitoring: 'Monitoring',
                logs: 'Logs',
                settings: 'Settings',
                total_projects: 'Total Projects',
                running_projects: 'Running Projects',
                stopped_projects: 'Stopped Projects',
                system_uptime: 'System Uptime',
                add_project: 'Add Project',
                project_name: 'Project Name',
                working_directory: 'Working Directory',
                command: 'Command',
                arguments: 'Arguments',
                log_path: 'Log Path',
                start: 'Start',
                stop: 'Stop',
                restart: 'Restart',
                edit: 'Edit',
                delete: 'Delete',
                running: 'Running',
                stopped: 'Stopped',
                error: 'Error'
            }
        };
    }

    get(key) {
        return this.translations[this.currentLanguage][key] || key;
    }

    setLanguage(lang) {
        this.currentLanguage = lang;
        localStorage.setItem('language', lang);
        document.documentElement.lang = lang;
        document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    }
}

class NextGenDashboard {
    constructor() {
        this.lang = new LanguageManager();
        this.projects = [];
        this.charts = {};
        this.ws = null;
        this.currentSection = 'overview';
        this.activityLog = [];
        this.performanceData = {
            labels: [],
            cpu: [],
            memory: []
        };
        this.init();
    }

    init() {
        this.setupEventListeners();
        // Apply saved language on load
        const sel = document.getElementById('language-selector');
        if (sel) sel.value = this.lang.currentLanguage;
        this.changeLanguage(this.lang.currentLanguage);

        this.initializeCharts();
        this.loadProjects();
        this.connectWebSocket();
        this.startPerformanceMonitoring();
        this.updateLastUpdateTime();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.currentTarget.getAttribute('href').substring(1);
                this.showSection(section);
            });
        });

        // Sidebar toggle
        document.getElementById('sidebar-toggle')?.addEventListener('click', () => {
            this.toggleSidebar();
        });

        // Project modal
        document.getElementById('add-project-btn')?.addEventListener('click', () => {
            this.showProjectModal();
        });

        document.getElementById('cancel-project-btn')?.addEventListener('click', () => {
            this.hideProjectModal();
        });

        // Language selector
        document.getElementById('language-selector')?.addEventListener('change', (e) => {
            this.changeLanguage(e.target.value);
        });

        document.getElementById('project-form')?.addEventListener('submit', (e) => {
            this.handleProjectSubmit(e);
        });

        // Folder selection
        document.getElementById('select-folder-btn')?.addEventListener('click', () => {
            this.selectProjectFolder();
        });

        // Log controls
        document.getElementById('log-project-select')?.addEventListener('change', () => {
            this.loadLogs();
        });

        document.getElementById('clear-logs-btn')?.addEventListener('click', () => {
            this.clearLogs();
        });
    }

    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('main > section').forEach(section => {
            section.classList.add('hidden');
        });

        // Show target section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.remove('hidden');
            this.currentSection = sectionName;
        }

        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('bg-slate-700/50');
        });
        document.querySelector(`[href="#${sectionName}"]`)?.classList.add('bg-slate-700/50');

        // Load section-specific data
        if (sectionName === 'logs') {
            this.loadLogs();
        } else if (sectionName === 'monitoring') {
            this.updateMonitoringCharts();
        }
    }

    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.getElementById('main-content');
        
        sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('expanded');
    }

    initializeCharts() {
        // Performance Chart
        const performanceCtx = document.getElementById('performance-chart')?.getContext('2d');
        if (performanceCtx) {
            this.charts.performance = new Chart(performanceCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'استخدام المعالج (%)',
                        data: [],
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4
                    }, {
                        label: 'استخدام الذاكرة (MB)',
                        data: [],
                        borderColor: '#8b5cf6',
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y1'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: '#e2e8f0' }
                        }
                    },
                    scales: {
                        x: {
                            ticks: { color: '#94a3b8' },
                            grid: { color: 'rgba(148, 163, 184, 0.1)' }
                        },
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            ticks: { color: '#94a3b8' },
                            grid: { color: 'rgba(148, 163, 184, 0.1)' }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            ticks: { color: '#94a3b8' },
                            grid: { drawOnChartArea: false }
                        }
                    }
                }
            });
        }

        // Status Chart
        const statusCtx = document.getElementById('status-chart')?.getContext('2d');
        if (statusCtx) {
            this.charts.status = new Chart(statusCtx, {
                type: 'doughnut',
                data: {
                    labels: ['قيد التشغيل', 'متوقف', 'خطأ', 'غير صحي'],
                    datasets: [{
                        data: [0, 0, 0, 0],
                        backgroundColor: [
                            '#10b981',
                            '#64748b',
                            '#ef4444',
                            '#f59e0b'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#e2e8f0' }
                        }
                    }
                }
            });
        }

        // Resource Timeline Chart
        const resourceCtx = document.getElementById('resource-timeline-chart')?.getContext('2d');
        if (resourceCtx) {
            this.charts.resourceTimeline = new Chart(resourceCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'استخدام المعالج',
                        data: [],
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: '#e2e8f0' }
                        }
                    },
                    scales: {
                        x: {
                            ticks: { color: '#94a3b8' },
                            grid: { color: 'rgba(148, 163, 184, 0.1)' }
                        },
                        y: {
                            ticks: { color: '#94a3b8' },
                            grid: { color: 'rgba(148, 163, 184, 0.1)' }
                        }
                    }
                }
            });
        }

        // Errors Chart
        const errorsCtx = document.getElementById('errors-chart')?.getContext('2d');
        if (errorsCtx) {
            this.charts.errors = new Chart(errorsCtx, {
                type: 'bar',
                data: {
                    labels: ['اليوم', 'أمس', 'منذ يومين', 'منذ 3 أيام', 'منذ 4 أيام'],
                    datasets: [{
                        label: 'عدد الأخطاء',
                        data: [12, 8, 15, 6, 9],
                        backgroundColor: 'rgba(239, 68, 68, 0.8)',
                        borderColor: '#ef4444',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: { color: '#e2e8f0' }
                        }
                    },
                    scales: {
                        x: {
                            ticks: { color: '#94a3b8' },
                            grid: { color: 'rgba(148, 163, 184, 0.1)' }
                        },
                        y: {
                            ticks: { color: '#94a3b8' },
                            grid: { color: 'rgba(148, 163, 184, 0.1)' }
                        }
                    }
                }
            });
        }
    }

    async loadProjects() {
        try {
            const response = await fetch('/api/projects');
            this.projects = await response.json();
            this.updateDashboard();
            
            // Also load system metrics
            this.loadSystemMetrics();
        } catch (error) {
            console.error('Error loading projects:', error);
            this.showNotification('خطأ في تحميل المشاريع', 'error');
        }
    }

    async loadSystemMetrics() {
        try {
            const response = await fetch('/api/system/metrics');
            const metrics = await response.json();
            this.updateSystemMetrics(metrics);
        } catch (error) {
            console.error('Error loading system metrics:', error);
        }
    }

    updateSystemMetrics(metrics) {
        // Update system CPU and memory displays
        const cpuElement = document.getElementById('cpu-usage');
        const memoryElement = document.getElementById('memory-usage');
        const cpuBar = document.getElementById('cpu-bar');
        const memoryBar = document.getElementById('memory-bar');
        
        if (cpuElement && metrics.cpu) {
            cpuElement.textContent = `${metrics.cpu.percent}%`;
        }
        
        if (memoryElement && metrics.memory) {
            memoryElement.textContent = `${metrics.memory.used_gb.toFixed(1)} GB`;
        }
        
        if (cpuBar && metrics.cpu) {
            cpuBar.style.width = `${metrics.cpu.percent}%`;
        }
        
        if (memoryBar && metrics.memory) {
            memoryBar.style.width = `${metrics.memory.percent}%`;
        }
    }

    updateDashboard() {
        this.updateOverviewStats();
        this.updateProjectsGrid();
        this.updateStatusChart();
        this.updateActivityFeed();
        this.updateLogProjectSelect();
    }

    updateOverviewStats() {
        const totalProjects = this.projects.length;
        const runningProjects = this.projects.filter(p => p.runtime.status === 'running').length;
        const totalCpu = this.projects.reduce((sum, p) => sum + (p.runtime.metrics.cpu_percent || 0), 0);
        const totalMemory = this.projects.reduce((sum, p) => sum + (p.runtime.metrics.memory_rss_mb || 0), 0);

        document.getElementById('total-projects').textContent = totalProjects;
        document.getElementById('running-projects').textContent = runningProjects;
        document.getElementById('cpu-usage').textContent = `${totalCpu.toFixed(1)}%`;
        document.getElementById('memory-usage').textContent = `${Math.round(totalMemory)} MB`;

        // Update progress bars
        const cpuPercentage = Math.min(totalCpu, 100);
        const memoryPercentage = Math.min((totalMemory / 8192) * 100, 100); // Assuming 8GB max
        
        document.getElementById('cpu-bar').style.width = `${cpuPercentage}%`;
        document.getElementById('memory-bar').style.width = `${memoryPercentage}%`;
    }

    updateProjectsGrid() {
        const grid = document.getElementById('projects-grid');
        if (!grid) return;

        grid.innerHTML = this.projects.map(project => this.createProjectCard(project)).join('');
        
        // Add event listeners to project cards
        grid.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const action = e.currentTarget.getAttribute('data-action');
                const projectId = e.currentTarget.getAttribute('data-project-id');
                if (action === 'edit') {
                    const proj = this.projects.find(p => p.config.id === projectId);
                    this.showProjectModal(proj);
                    return;
                }
                if (action === 'delete') {
                    if (confirm('هل تريد حذف هذا المشروع؟')) {
                        const resp = await fetch(`/api/projects/${projectId}`, { method: 'DELETE' });
                        if (resp.ok) {
                            this.showNotification('تم حذف المشروع', 'success');
                            this.loadProjects();
                        } else {
                            this.showNotification('فشل حذف المشروع', 'error');
                        }
                    }
                    return;
                }
                this.handleProjectAction(action, projectId);
            });
        });
    }

    showProjectModal(project = null) {
        const modal = document.getElementById('project-modal');
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        // If edit, prefill form
        if (project) {
            const form = document.getElementById('project-form');
            form.querySelector('[name="id"]').value = project.config.id;
            form.querySelector('[name="name"]').value = project.config.name;
            form.querySelector('[name="working_dir"]').value = project.config.working_dir;
            form.querySelector('[name="command"]').value = project.config.command;
            form.querySelector('[name="args"]').value = (project.config.args||[]).join(' ');
            form.querySelector('[name="instances"]').value = project.config.instances || 1;
            form.querySelector('[name="port"]').value = (project.config.ports||[])[0] || '';
            form.querySelector('[name="log_path"]').value = project.config.log_path || '';
            form.querySelector('[name="description"]').value = project.config.description || '';
        }
    }

    async verifyWorkingDir(workingDir){
        try {
            const resp = await fetch('/api/projects/verify-path', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ working_dir: workingDir })
            });
            if (!resp.ok) return { exists: false };
            return await resp.json();
        } catch {
            return { exists: false };
        }
    }

    createProjectCard(project) {
        const config = project.config;
        const runtime = project.runtime;
        const statusColors = {
            running: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
            stopped: 'bg-slate-500/20 text-slate-300 border-slate-500/30',
            unhealthy: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
            crashed: 'bg-red-500/20 text-red-300 border-red-500/30'
        };
        const healthColors = { healthy: 'text-emerald-400', unhealthy: 'text-yellow-400', unknown: 'text-slate-400' };
        const statusEmoji = { running: '🟢', stopped: '🔴', unhealthy: '🟡', crashed: '🔴' }[runtime.status] || '⚪';
        return `
            <div class="glass-effect rounded-xl p-6 border border-slate-700/50 hover:border-slate-600/50 transition-all">
                <div class="flex items-center justify-between mb-4">
                    <div>
                        <h3 class="text-lg font-semibold text-white">${statusEmoji} ${config.name}</h3>
                        <p class="text-sm text-slate-400">${config.command} ${(config.args||[]).join(' ')}</p>
                        <p class="text-xs text-slate-500 mt-1">${config.working_dir}</p>
                    </div>
                    <span class="px-3 py-1 rounded-full text-xs border ${statusColors[runtime.status] || statusColors.stopped}">${runtime.status}</span>
                </div>
                <div class="flex items-center gap-2 mb-2">
                    <button data-action="edit" data-project-id="${config.id}" class="px-2 py-1 text-xs rounded bg-slate-700 hover:bg-slate-600">${this.lang.get('edit')}</button>
                    <button data-action="delete" data-project-id="${config.id}" class="px-2 py-1 text-xs rounded bg-red-700 hover:bg-red-600">${this.lang.get('delete')}</button>
                </div>
                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div class="bg-slate-800/50 rounded-lg p-3">
                        <div class="text-xs text-slate-400">CPU</div>
                        <div class="text-lg font-semibold text-emerald-400">${(runtime.metrics.cpu_percent || 0).toFixed(1)}%</div>
                    </div>
                    <div class="bg-slate-800/50 rounded-lg p-3">
                        <div class="text-xs text-slate-400">Memory</div>
                        <div class="text-lg font-semibold text-purple-400">${Math.round(runtime.metrics.memory_rss_mb || 0)} MB</div>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <button data-action="start" data-project-id="${config.id}" class="flex-1 bg-emerald-600 hover:bg-emerald-700 px-3 py-2 rounded-lg text-sm transition-colors" ${runtime.status === 'running' ? 'disabled' : ''}>${this.lang.get('start')}</button>
                    <button data-action="stop" data-project-id="${config.id}" class="flex-1 bg-red-600 hover:bg-red-700 px-3 py-2 rounded-lg text-sm transition-colors" ${runtime.status === 'stopped' ? 'disabled' : ''}>${this.lang.get('stop')}</button>
                    <button data-action="restart" data-project-id="${config.id}" class="flex-1 bg-yellow-600 hover:bg-yellow-700 px-3 py-2 rounded-lg text-sm transition-colors">${this.lang.get('restart')}</button>
                </div>
            </div>
        `;
    }

    formatUptime(seconds) {
        if (!seconds) return 'غير متاح';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (hours > 0) {
            return `${hours}س ${minutes}د`;
        } else {
            return `${minutes}د`;
        }
    }

    updateStatusChart() {
        if (!this.charts.status) return;

        const statusCounts = {
            running: 0,
            stopped: 0,
            crashed: 0,
            unhealthy: 0
        };

        this.projects.forEach(project => {
            const status = project.runtime.status;
            if (status === 'running') {
                if (project.runtime.health?.status === 'unhealthy') {
                    statusCounts.unhealthy++;
                } else {
                    statusCounts.running++;
                }
            } else if (status === 'crashed') {
                statusCounts.crashed++;
            } else {
                statusCounts.stopped++;
            }
        });

        this.charts.status.data.datasets[0].data = [
            statusCounts.running,
            statusCounts.stopped,
            statusCounts.crashed,
            statusCounts.unhealthy
        ];
        this.charts.status.update();
    }

    updateActivityFeed() {
        const feed = document.getElementById('activity-feed');
        if (!feed) return;

        // Generate sample activity data
        const activities = [
            { time: '2 دقائق', action: 'تم تشغيل', project: 'نظام الحضور', icon: 'fa-play', color: 'text-emerald-400' },
            { time: '5 دقائق', action: 'إعادة تشغيل', project: 'نظام الكول سنتر', icon: 'fa-redo', color: 'text-yellow-400' },
            { time: '10 دقائق', action: 'تم إيقاف', project: 'واجهة المستخدم', icon: 'fa-stop', color: 'text-red-400' },
            { time: '15 دقيقة', action: 'تم إضافة', project: 'مشروع جديد', icon: 'fa-plus', color: 'text-blue-400' }
        ];

        feed.innerHTML = activities.map(activity => `
            <div class="flex items-center gap-3 p-3 bg-slate-800/30 rounded-lg">
                <div class="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center">
                    <i class="fas ${activity.icon} text-xs ${activity.color}"></i>
                </div>
                <div class="flex-1">
                    <div class="text-sm text-white">${activity.action} ${activity.project}</div>
                    <div class="text-xs text-slate-400">منذ ${activity.time}</div>
                </div>
            </div>
        `).join('');
    }

    updateLogProjectSelect() {
        const select = document.getElementById('log-project-select');
        if (!select) return;

        const options = this.projects.map(project => 
            `<option value="${project.config.id}">${project.config.name}</option>`
        ).join('');
        
        select.innerHTML = `<option value="">جميع المشاريع</option>${options}`;
    }

    async handleProjectAction(action, projectId) {
        try {
            let response;
            switch (action) {
                case 'start':
                    response = await fetch(`/api/projects/${projectId}/start`, { method: 'POST' });
                    break;
                case 'stop':
                    response = await fetch(`/api/projects/${projectId}/stop`, { method: 'POST' });
                    break;
                case 'restart':
                    response = await fetch(`/api/projects/${projectId}/restart`, { method: 'POST' });
                    break;
            }

            if (response && response.ok) {
                this.showNotification(`تم ${action} المشروع بنجاح`, 'success');
                this.loadProjects();
            } else {
                throw new Error('فشل في تنفيذ العملية');
            }
        } catch (error) {
            console.error('Error handling project action:', error);
            this.showNotification('خطأ في تنفيذ العملية', 'error');
        }
    }

    hideProjectModal() {
        document.getElementById('project-modal').classList.add('hidden');
        document.getElementById('project-modal').classList.remove('flex');
        document.getElementById('project-form').reset();
    }

    async handleProjectSubmit(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const working_dir = formData.get('working_dir');
        const verify = await this.verifyWorkingDir(working_dir);
        if (!verify.exists || !verify.is_dir) {
            this.showNotification('مسار مجلد العمل غير موجود على الخادم', 'error');
            return;
        }
        
        const config = {
            id: formData.get('id'),
            name: formData.get('name'),
            working_dir,
            command: formData.get('command') || 'python',
            args: (formData.get('args') || '').split(' ').filter(Boolean),
            instances: parseInt(formData.get('instances')) || 1,
            log_path: formData.get('log_path') || null,
            ports: formData.get('port') ? [parseInt(formData.get('port'))] : [],
            description: formData.get('description') || '',
            env: {},
            healthcheck: { type: 'process', interval_seconds: 10, timeout_seconds: 3 },
            restart_policy: { autorestart: true, restart_delay_seconds: 5, max_restarts_per_hour: 10 },
            start_on_boot: false,
            actions: {}
        };

        try {
            const response = await fetch('/api/projects', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ config })
            });

            if (response.ok) {
                this.showNotification('تم حفظ المشروع بنجاح', 'success');
                this.hideProjectModal();
                this.loadProjects();
            } else {
                throw new Error('فشل في حفظ المشروع');
            }
        } catch (error) {
            console.error('Error creating project:', error);
            this.showNotification('خطأ في حفظ المشروع', 'error');
        }
    }

    async loadLogs() {
        const projectId = document.getElementById('log-project-select')?.value;
        const container = document.getElementById('logs-container');
        
        if (!container) return;

        try {
            if (projectId) {
                const response = await fetch(`/api/projects/${projectId}/logs?lines=1000`);
                const data = await response.json();
                container.innerHTML = data.lines.map(line => 
                    `<div class="text-slate-300 py-1">${this.escapeHtml(line)}</div>`
                ).join('');
            } else {
                container.innerHTML = '<div class="text-slate-400">اختر مشروعاً لعرض السجلات</div>';
            }
            
            container.scrollTop = container.scrollHeight;
        } catch (error) {
            console.error('Error loading logs:', error);
            container.innerHTML = '<div class="text-red-400">خطأ في تحميل السجلات</div>';
        }
    }

    clearLogs() {
        const container = document.getElementById('logs-container');
        if (container) {
            container.innerHTML = '<div class="text-slate-400">تم مسح السجلات</div>';
        }
    }

    connectWebSocket() {
        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onmessage = (event) => {
            try {
                this.projects = JSON.parse(event.data);
                this.updateDashboard();
                this.updatePerformanceChart();
            } catch (error) {
                console.error('Error parsing WebSocket data:', error);
            }
        };
        
        this.ws.onclose = () => {
            setTimeout(() => this.connectWebSocket(), 2000);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    startPerformanceMonitoring() {
        // Update system metrics every 5 seconds
        setInterval(() => {
            this.loadSystemMetrics();
        }, 5000);
        
        // Update projects every 10 seconds
        setInterval(() => {
            this.loadProjects();
        }, 10000);
    }

    updatePerformanceData() {
        const now = new Date();
        const timeLabel = now.toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' });
        
        // Get system metrics for performance chart
        fetch('/api/system/metrics')
            .then(response => response.json())
            .then(metrics => {
                const cpuValue = metrics.cpu?.percent || 0;
                const memoryValue = metrics.memory?.percent || 0;
                
                this.performanceData.labels.push(timeLabel);
                this.performanceData.cpu.push(cpuValue);
                this.performanceData.memory.push(memoryValue);
                
                // Keep only last 20 data points
                if (this.performanceData.labels.length > 20) {
                    this.performanceData.labels.shift();
                    this.performanceData.cpu.shift();
                    this.performanceData.memory.shift();
                }
                
                this.updatePerformanceChart();
            })
            .catch(error => {
                console.error('Error updating performance data:', error);
            });
    }

    updatePerformanceChart() {
        if (!this.charts.performance) return;
        
        this.charts.performance.data.labels = this.performanceData.labels;
        this.charts.performance.data.datasets[0].data = this.performanceData.cpu;
        this.charts.performance.data.datasets[1].data = this.performanceData.memory;
        this.charts.performance.update('none');
    }

    updateMonitoringCharts() {
        // Update resource timeline chart
        if (this.charts.resourceTimeline) {
            this.charts.resourceTimeline.data.labels = this.performanceData.labels;
            this.charts.resourceTimeline.data.datasets[0].data = this.performanceData.cpu;
            this.charts.resourceTimeline.update();
        }
    }

    updateLastUpdateTime() {
        const updateTime = () => {
            const now = new Date();
            const timeString = now.toLocaleTimeString('ar-SA');
            const element = document.getElementById('last-update');
            if (element) {
                element.textContent = timeString;
            }
        };
        
        updateTime();
        setInterval(updateTime, 1000);
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 left-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full`;
        
        const colors = {
            success: 'bg-emerald-600 text-white',
            error: 'bg-red-600 text-white',
            info: 'bg-blue-600 text-white',
            warning: 'bg-yellow-600 text-white'
        };
        
        notification.className += ` ${colors[type] || colors.info}`;
        notification.innerHTML = `
            <div class="flex items-center gap-3">
                <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'}-circle"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    changeLanguage(lang) {
        this.lang.setLanguage(lang);
        // Update page title and main elements
        document.title = `${this.lang.get('app_title')} - ${this.lang.get('subtitle')}`;
        const h1 = document.querySelector('h1');
        if (h1) {
            h1.textContent = this.lang.get('app_title');
            const sub = h1.nextElementSibling;
            if (sub) sub.textContent = this.lang.get('subtitle');
        }
        const statusText = document.querySelector('.status-indicator')?.nextElementSibling;
        if (statusText) statusText.textContent = this.lang.get('system_connected');
        // Update navigation
        const navLinks = document.querySelectorAll('.nav-link');
        const keys = ['overview','projects','monitoring','logs','settings'];
        navLinks.forEach((link, i) => {
            const icon = link.querySelector('i');
            if (icon) link.innerHTML = `${icon.outerHTML} ${this.lang.get(keys[i])}`;
        });
        // Sync selector UI
        const sel = document.getElementById('language-selector');
        if (sel) sel.value = lang;
        // Re-render dashboard content with translated labels where applicable
        this.updateDashboard();
    }

    async selectProjectFolder() {
        // Create a simple input dialog for folder path
        const folderPath = prompt('أدخل مسار مجلد المشروع:');
        if (!folderPath) return;
        
        try {
            // Update the working directory field
            const workingDirInput = document.getElementById('working_dir');
            if (workingDirInput) {
                workingDirInput.value = folderPath;
            }
            
            // Auto-detect project files using API
            await this.detectProjectFiles(folderPath);
        } catch (error) {
            console.error('Error selecting folder:', error);
            this.showNotification('خطأ في اختيار المجلد', 'error');
        }
    }

    async detectProjectFiles(folderPath) {
        try {
            const response = await fetch('/api/detect-project-files', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folder_path: folderPath })
            });
            
            if (!response.ok) {
                throw new Error('فشل في الكشف عن ملفات المشروع');
            }
            
            const data = await response.json();
            
            // Update form fields with detected values
            const commandInput = document.getElementById('command');
            const argsInput = document.getElementById('args');
            const logPathInput = document.querySelector('input[name="log_path"]');
            
            if (data.command && commandInput) {
                commandInput.value = data.command;
            }
            
            if (data.main_file && argsInput) {
                if (data.command === 'npm' && data.main_file === 'package.json') {
                    argsInput.value = 'start';
                } else {
                    argsInput.value = data.main_file;
                }
            }
            
            if (data.log_path && logPathInput) {
                logPathInput.value = `${folderPath}/${data.log_path}`;
            }
            
            this.showNotification(`تم الكشف عن ملفات المشروع تلقائياً: ${data.detected_files.length} ملف`, 'success');
        } catch (error) {
            console.error('Error detecting project files:', error);
            this.showNotification('خطأ في الكشف عن ملفات المشروع', 'error');
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new NextGenDashboard();
});