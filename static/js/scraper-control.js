/**
 * Scraper Control Module
 * Provides UI controls for scheduler and manual scraping
 */

function scraperControl() {
    return {
        // Scheduler state
        schedulerStatus: 'Desconocido',
        schedulerStatusClass: 'status-stopped',
        schedulerRunning: false,
        schedulerPaused: false,
        jobCount: 0,
        totalExecutions: 0,
        lastHeartbeat: '-',
        
        // Jobs and executions
        jobs: [],
        executions: [],
        activeExecutions: [],
        executionHistory: [],
        predefinedJobs: {},
        
        // Modal de Detalles de Ejecución
        showDetailsModal: false,
        selectedExecution: null,
        selectedExecutionLogs: [],
        
        // Manual scraping
        manualConfig: {
            operacion: 'venta',
            tipo: 'departamento',
            max_pages: 10,
            max_properties: 0,
            formato: 'json',
            scrape_details: true,
            verbose: false
        },
        manualScraping: false,
        manualResult: null,
        manualSuccess: false,
        scrapingId: null,
        scrapingLogs: [],
        // Live stats for the current manual execution
        liveStats: {
            properties_scraped: 0,
            properties_new: 0,
            pages_processed: 0,
            status: null,
            start_time: null,
            duration: 0
        },
        liveLastLogId: 0,
        livePollHandle: null,
        liveDurationHandle: null,
        autoScrollLogs: true,
        
        // Add job form
        showAddJobForm: false,
        newJob: {
            operacion: 'venta',
            tipo: 'departamento',
            schedule_type: 'cron',
            hours: 1,
            hour: 2,
            minute: 0
        },
        
        // Socket.IO
        socket: null,
        
        init() {
            this.refreshStatus();
            this.loadPredefinedJobs();
            this.refreshExecutionHistory();
            // Auto-refresh every 30 seconds
            setInterval(() => this.refreshStatus(), 30000);
            // Refresh active executions every 10 seconds
            setInterval(() => this.refreshActiveExecutions(), 10000);
            // Refresh execution history every 60 seconds
            setInterval(() => this.refreshExecutionHistory(), 60000);
            
            // Initialize Socket.IO connection
            this.initSocket();
        },
        
        initSocket() {
            if (typeof io !== 'undefined') {
                this.socket = io();
                
                this.socket.on('scraping_log', (data) => {
                    // Backend emits 'execution_id' (legacy clients read 'scraping_id')
                    const id = data.execution_id || data.scraping_id;
                    if (id === this.scrapingId) {
                        this.appendLog({
                            timestamp: data.timestamp,
                            log: data.log
                        });
                    }
                });
                
                this.socket.on('scraping_complete', (data) => {
                    const id = data.execution_id || data.scraping_id;
                    if (id === this.scrapingId) {
                        this.finalizeManualRun(data.return_code === 0 ? 'completed' : 'failed', data.timestamp);
                    }
                });
                
                this.socket.on('scraping_error', (data) => {
                    const id = data.execution_id || data.scraping_id;
                    if (id === this.scrapingId) {
                        this.manualScraping = false;
                        this.manualSuccess = false;
                        this.manualResult = `Error: ${data.error}`;
                        this.appendLog({
                            timestamp: data.timestamp,
                            log: `=== ERROR: ${data.error} ===`
                        });
                        this.stopLivePolling();
                    }
                });
            }
        },
        
        // Scheduler controls
        async startScheduler() {
            try {
                const response = await fetch('/api/scheduler/start', {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.status === 'success') {
                    alert('Scheduler iniciado exitosamente');
                    this.refreshStatus();
                } else {
                    alert('Error: ' + data.message);
                }
            } catch (error) {
                alert('Error al iniciar scheduler: ' + error.message);
            }
        },
        
        async pauseScheduler() {
            try {
                const response = await fetch('/api/scheduler/pause', {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.status === 'success') {
                    alert('Scheduler pausado exitosamente');
                    this.refreshStatus();
                } else {
                    alert('Error: ' + data.message);
                }
            } catch (error) {
                alert('Error al pausar scheduler: ' + error.message);
            }
        },
        
        async resumeScheduler() {
            try {
                const response = await fetch('/api/scheduler/resume', {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.status === 'success') {
                    alert('Scheduler reanudado exitosamente');
                    this.refreshStatus();
                } else {
                    alert('Error: ' + data.message);
                }
            } catch (error) {
                alert('Error al reanudar scheduler: ' + error.message);
            }
        },
        
        async stopScheduler() {
            if (!confirm('¿Estás seguro de detener el scheduler?')) {
                return;
            }
            
            try {
                const response = await fetch('/api/scheduler/stop', {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.status === 'success') {
                    alert('Scheduler detenido exitosamente');
                    this.refreshStatus();
                } else {
                    alert('Error: ' + data.message);
                }
            } catch (error) {
                alert('Error al detener scheduler: ' + error.message);
            }
        },
        
        async refreshStatus() {
            try {
                // Get scheduler status
                const statusResponse = await fetch('/api/scheduler/status');
                const statusData = await statusResponse.json();
                
                if (statusData.status === 'success') {
                    const state = statusData.data.state;
                    this.schedulerRunning = statusData.data.is_running;
                    this.schedulerPaused = state && state.status === 'paused';
                    
                    if (this.schedulerRunning && !this.schedulerPaused) {
                        this.schedulerStatus = 'En ejecución';
                        this.schedulerStatusClass = 'status-running';
                    } else if (this.schedulerPaused) {
                        this.schedulerStatus = 'Pausado';
                        this.schedulerStatusClass = 'status-paused';
                    } else {
                        this.schedulerStatus = 'Detenido';
                        this.schedulerStatusClass = 'status-stopped';
                    }
                    
                    this.jobCount = statusData.data.jobs.length;
                    this.totalExecutions = state ? state.total_jobs_executed : 0;
                    
                    if (state && state.last_heartbeat) {
                        this.lastHeartbeat = this.formatDate(state.last_heartbeat);
                    }
                    
                    this.jobs = statusData.data.jobs;
                }
                
                // Get executions
                const execResponse = await fetch('/api/scheduler/executions?limit=20');
                const execData = await execResponse.json();
                
                if (execData.status === 'success') {
                    this.executions = execData.data;
                }
                
                // Get active executions
                await this.refreshActiveExecutions();
            } catch (error) {
                console.error('Error refreshing status:', error);
            }
        },
        
        async refreshActiveExecutions() {
            try {
                const response = await fetch('/api/scraper/executions?status=running&limit=10');
                const data = await response.json();
                
                if (data.status === 'success') {
                    this.activeExecutions = data.data;
                }
            } catch (error) {
                console.error('Error refreshing active executions:', error);
            }
        },
        
        async refreshExecutionHistory() {
            try {
                const response = await fetch('/api/scraper/executions?per_page=50');
                const data = await response.json();
                
                if (data.status === 'success') {
                    this.executionHistory = data.data;
                }
            } catch (error) {
                console.error('Error refreshing execution history:', error);
            }
        },
        
        async showExecutionDetails(executionId) {
            this.selectedExecution = null;
            this.selectedExecutionLogs = [];
            this.showDetailsModal = true;
            
            try {
                const response = await fetch(`/api/scraper/executions/${executionId}`);
                const data = await response.json();
                
                if (data.success && data.data) {
                    this.selectedExecution = data.data;
                    if (data.data.logs) {
                        this.selectedExecutionLogs = data.data.logs;
                    }
                } else {
                    alert('Error al cargar detalles de la ejecución: ' + (data.error || 'Desconocido'));
                    this.showDetailsModal = false;
                }
            } catch (error) {
                console.error('Error fetching execution details:', error);
                alert('No se pudo establecer conexión para cargar los detalles.');
                this.showDetailsModal = false;
            }
        },
        
        async loadPredefinedJobs() {
            try {
                const response = await fetch('/api/scheduler/jobs/predefined');
                const data = await response.json();
                
                if (data.status === 'success') {
                    this.predefinedJobs = data.data.configurations;
                }
            } catch (error) {
                console.error('Error loading predefined jobs:', error);
            }
        },
        
        async addPredefinedJob(jobName) {
            try {
                const response = await fetch(`/api/scheduler/jobs/predefined/${jobName}`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.status === 'success') {
                    alert(`Job "${jobName}" agregado exitosamente`);
                    this.refreshStatus();
                } else {
                    alert('Error: ' + data.message);
                }
            } catch (error) {
                alert('Error al agregar job predefinido: ' + error.message);
            }
        },
        
        isJobActive(jobName) {
            // Check if a job with this name is already active
            return this.jobs.some(job => job.id.includes(jobName) || job.name.includes(jobName));
        },
        
        formatJobName(jobName) {
            return jobName
                .split('_')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ');
        },
        
        getTimeUntil(dateStr) {
            if (!dateStr) return '';
            
            const now = new Date();
            const target = new Date(dateStr);
            const diff = target - now;
            
            if (diff < 0) return 'Vencido';
            
            const hours = Math.floor(diff / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            
            if (hours > 24) {
                const days = Math.floor(hours / 24);
                return `En ${days}d ${hours % 24}h`;
            } else if (hours > 0) {
                return `En ${hours}h ${minutes}m`;
            } else {
                return `En ${minutes}m`;
            }
        },
        
        // Job controls
        async pauseJob(jobId) {
            try {
                const response = await fetch(`/api/scheduler/jobs/${jobId}/pause`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.status === 'success') {
                    alert('Job pausado exitosamente');
                    this.refreshStatus();
                } else {
                    alert('Error: ' + data.message);
                }
            } catch (error) {
                alert('Error al pausar job: ' + error.message);
            }
        },
        
        async resumeJob(jobId) {
            try {
                const response = await fetch(`/api/scheduler/jobs/${jobId}/resume`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.status === 'success') {
                    alert('Job reanudado exitosamente');
                    this.refreshStatus();
                } else {
                    alert('Error: ' + data.message);
                }
            } catch (error) {
                alert('Error al reanudar job: ' + error.message);
            }
        },
        
        async removeJob(jobId) {
            if (!confirm('¿Estás seguro de eliminar este job?')) {
                return;
            }
            
            try {
                const response = await fetch(`/api/scheduler/jobs/${jobId}`, {
                    method: 'DELETE'
                });
                const data = await response.json();
                
                if (data.status === 'success') {
                    alert('Job eliminado exitosamente');
                    this.refreshStatus();
                } else {
                    alert('Error: ' + data.message);
                }
            } catch (error) {
                alert('Error al eliminar job: ' + error.message);
            }
        },
        
        async addJob() {
            const scheduleArgs = {};
            
            if (this.newJob.schedule_type === 'interval') {
                scheduleArgs.hours = parseInt(this.newJob.hours);
            } else {
                scheduleArgs.hour = parseInt(this.newJob.hour);
                scheduleArgs.minute = parseInt(this.newJob.minute);
            }
            
            const jobData = {
                operacion: this.newJob.operacion,
                tipo: this.newJob.tipo,
                schedule_type: this.newJob.schedule_type,
                schedule_args: scheduleArgs,
                max_pages: 50,
                scrape_details: true,
                max_detail_properties: 100
            };
            
            try {
                const response = await fetch('/api/scheduler/jobs', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(jobData)
                });
                const data = await response.json();
                
                if (data.status === 'success') {
                    alert('Job agregado exitosamente');
                    this.showAddJobForm = false;
                    this.refreshStatus();
                } else {
                    alert('Error: ' + data.message);
                }
            } catch (error) {
                alert('Error al agregar job: ' + error.message);
            }
        },
        
        // Manual scraping
        async runManualScraping() {
            this.manualScraping = true;
            this.manualResult = null;
            this.scrapingLogs = [];
            
            const requestBody = {
                operacion: this.manualConfig.operacion,
                tipo: this.manualConfig.tipo,
                max_pages: this.manualConfig.max_pages,
                max_properties: parseInt(this.manualConfig.max_properties) || 0,
                formato: this.manualConfig.formato,
                scrape_details: this.manualConfig.scrape_details,
                verbose: this.manualConfig.verbose
            };
            
            try {
                const response = await fetch('/api/scraper/run', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(requestBody)
                });
                
                const data = await response.json();
                
                if (data.success === true) {
                    this.scrapingId = data.data.execution_id;
                    this.manualSuccess = true;
                    this.manualResult = data.message;
                    this.liveLastLogId = 0;
                    this.liveStats = {
                        properties_scraped: 0,
                        properties_new: 0,
                        pages_processed: 0,
                        status: 'running',
                        start_time: new Date().toISOString(),
                        duration: 0
                    };
                    this.appendLog({
                        timestamp: new Date().toISOString(),
                        log: `=== Iniciando scraping: ${this.manualConfig.operacion} ${this.manualConfig.tipo} ===`
                    });
                    
                    // Refresh active executions immediately to show the new one
                    await this.refreshActiveExecutions();
                    
                    // Start live polling (stats + incremental logs) as fallback/supplement to Socket.IO
                    this.startLivePolling(data.data.execution_id);
                } else {
                    this.manualScraping = false;
                    this.manualSuccess = false;
                    this.manualResult = 'Error: ' + (data.error || data.message);
                }
            } catch (error) {
                this.manualScraping = false;
                this.manualSuccess = false;
                this.manualResult = 'Error: ' + error.message;
            }
        },
        
        appendLog(entry) {
            this.scrapingLogs.push(entry);
            // Cap log buffer to avoid runaway memory
            if (this.scrapingLogs.length > 2000) {
                this.scrapingLogs.splice(0, this.scrapingLogs.length - 2000);
            }
            if (this.autoScrollLogs) {
                this.$nextTick(() => {
                    const logContainer = document.getElementById('log-container');
                    if (logContainer) {
                        logContainer.scrollTop = logContainer.scrollHeight;
                    }
                });
            }
        },
        
        clearScrapingLogs() {
            this.scrapingLogs = [];
        },
        
        startLivePolling(executionId) {
            this.stopLivePolling();
            
            // Tick duration every second
            this.liveDurationHandle = setInterval(() => {
                if (this.liveStats.start_time && this.liveStats.status === 'running') {
                    this.liveStats.duration = Math.floor(
                        (Date.now() - new Date(this.liveStats.start_time).getTime()) / 1000
                    );
                }
            }, 1000);
            
            // Poll live endpoint every 2s for stats + incremental logs
            const poll = async () => {
                try {
                    const url = `/api/scraper/executions/${executionId}/live?since=${this.liveLastLogId}`;
                    const response = await fetch(url);
                    const data = await response.json();
                    
                    if (!data.success || !data.data) return;
                    const d = data.data;
                    
                    // Update stats
                    this.liveStats.properties_scraped = d.properties_scraped || 0;
                    this.liveStats.properties_new = d.properties_new || 0;
                    this.liveStats.pages_processed = d.pages_processed || 0;
                    this.liveStats.status = d.status;
                    if (d.start_time) this.liveStats.start_time = d.start_time;
                    if (d.duration) this.liveStats.duration = d.duration;
                    
                    // Append new logs (Socket.IO may have covered some; dedupe by id)
                    if (Array.isArray(d.new_logs) && d.new_logs.length > 0) {
                        for (const log of d.new_logs) {
                            this.appendLog({
                                timestamp: log.timestamp,
                                log: log.message,
                                level: log.level
                            });
                        }
                    }
                    if (d.last_log_id) this.liveLastLogId = d.last_log_id;
                    
                    // Refresh active executions panel (lightweight)
                    this.refreshActiveExecutions();
                    
                    // Terminal states
                    if (['completed', 'failed', 'cancelled'].includes(d.status)) {
                        this.finalizeManualRun(d.status, new Date().toISOString(), d);
                    }
                } catch (error) {
                    console.error('Error en live polling:', error);
                }
            };
            
            poll();
            this.livePollHandle = setInterval(poll, 2000);
            
            // Safety: stop after 2h
            setTimeout(() => this.stopLivePolling(), 2 * 3600000);
        },
        
        stopLivePolling() {
            if (this.livePollHandle) {
                clearInterval(this.livePollHandle);
                this.livePollHandle = null;
            }
            if (this.liveDurationHandle) {
                clearInterval(this.liveDurationHandle);
                this.liveDurationHandle = null;
            }
        },
        
        finalizeManualRun(status, timestamp, execData) {
            if (!this.manualScraping && this.liveStats.status === status) return; // already finalized
            this.manualScraping = false;
            this.manualSuccess = status === 'completed';
            this.liveStats.status = status;
            
            const label = status === 'completed' ? 'completado'
                : status === 'cancelled' ? 'cancelado'
                : 'fallido';
            const props = (execData && execData.properties_scraped) || this.liveStats.properties_scraped || 0;
            const pages = (execData && execData.pages_processed) || this.liveStats.pages_processed || 0;
            this.manualResult = `Scraping ${label}. ${props} propiedades, ${pages} páginas.`;
            
            this.appendLog({
                timestamp: timestamp || new Date().toISOString(),
                log: `=== Scraping ${label} ===`
            });
            
            this.stopLivePolling();
            this.refreshActiveExecutions();
            this.refreshExecutionHistory();
        },
        
        async stopManualScraping() {
            if (!this.scrapingId) {
                alert('No hay ejecución activa para detener');
                return;
            }
            
            if (!confirm('¿Estás seguro de detener esta ejecución?')) {
                return;
            }
            
            try {
                const response = await fetch(`/api/scraper/executions/${this.scrapingId}/cancel`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.manualScraping = false;
                    this.manualSuccess = false;
                    this.manualResult = 'Ejecución cancelada por el usuario';
                    this.liveStats.status = 'cancelled';
                    this.appendLog({
                        timestamp: new Date().toISOString(),
                        log: '=== Ejecución cancelada por el usuario ==='
                    });
                    
                    this.stopLivePolling();
                    
                    // Refresh execution history
                    await this.refreshExecutionHistory();
                    await this.refreshActiveExecutions();
                } else {
                    alert('Error al cancelar: ' + (data.error || data.message));
                }
            } catch (error) {
                alert('Error al cancelar ejecución: ' + error.message);
            }
        },
        
        // Utility functions
        formatDate(dateStr) {
            if (!dateStr) return '-';
            
            const date = new Date(dateStr);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            
            // Si es reciente (< 1 hora), mostrar tiempo relativo
            if (diffMins < 60 && diffMins >= 0) {
                if (diffMins < 1) return 'Ahora';
                return `Hace ${diffMins}m`;
            }
            
            return date.toLocaleString('es-CL', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        },
        
        formatLogTime(timestamp) {
            if (!timestamp) return '';
            
            const date = new Date(timestamp);
            return date.toLocaleTimeString('es-CL', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        },
        
        formatTimeAgo(dateStr) {
            if (!dateStr) return '-';
            
            const date = new Date(dateStr);
            const now = new Date();
            const diffMs = now - date;
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMs / 3600000);
            const diffDays = Math.floor(diffMs / 86400000);
            
            if (diffMins < 1) return 'Ahora';
            if (diffMins < 60) return `Hace ${diffMins}m`;
            if (diffHours < 24) return `Hace ${diffHours}h`;
            if (diffDays < 7) return `Hace ${diffDays}d`;
            return `Hace ${Math.floor(diffDays / 7)}sem`;
        },
        
        formatDuration(seconds) {
            if (!seconds || seconds === 0) return '-';
            
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = seconds % 60;
            
            if (hours > 0) {
                return `${hours}h ${minutes}m`;
            } else if (minutes > 0) {
                return `${minutes}m ${secs}s`;
            } else {
                return `${secs}s`;
            }
        },
        
        getStatusClass(status) {
            const statusMap = {
                'running': 'bg-blue-100 text-blue-800',
                'completed': 'bg-green-100 text-green-800',
                'failed': 'bg-red-100 text-red-800',
                'cancelled': 'bg-yellow-100 text-yellow-800'
            };
            return statusMap[status] || 'bg-slate-100 text-slate-800';
        },
        
        getStatusLabel(status) {
            const labelMap = {
                'running': 'En ejecución',
                'completed': 'Completado',
                'failed': 'Fallido',
                'cancelled': 'Cancelado'
            };
            return labelMap[status] || status;
        }
    };
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Alpine.js will handle the initialization via x-data
    console.log('Scraper Control module loaded');
});
