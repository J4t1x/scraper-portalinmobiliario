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
        
        // Manual scraping
        manualConfig: {
            operacion: 'venta',
            tipo: 'departamento',
            max_pages: 10,
            formato: 'json',
            scrape_details: true,
            verbose: false
        },
        manualScraping: false,
        manualResult: null,
        manualSuccess: false,
        scrapingId: null,
        scrapingLogs: [],
        
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
            // Auto-refresh every 30 seconds
            setInterval(() => this.refreshStatus(), 30000);
            
            // Initialize Socket.IO connection
            this.initSocket();
        },
        
        initSocket() {
            if (typeof io !== 'undefined') {
                this.socket = io();
                
                this.socket.on('scraping_log', (data) => {
                    if (data.scraping_id === this.scrapingId) {
                        this.scrapingLogs.push({
                            timestamp: data.timestamp,
                            log: data.log
                        });
                        // Auto-scroll to bottom
                        this.$nextTick(() => {
                            const logContainer = document.getElementById('log-container');
                            if (logContainer) {
                                logContainer.scrollTop = logContainer.scrollHeight;
                            }
                        });
                    }
                });
                
                this.socket.on('scraping_complete', (data) => {
                    if (data.scraping_id === this.scrapingId) {
                        this.manualScraping = false;
                        this.manualSuccess = data.return_code === 0;
                        this.manualResult = `Scraping completado (código: ${data.return_code})`;
                        this.scrapingLogs.push({
                            timestamp: data.timestamp,
                            log: `=== Scraping completado (código: ${data.return_code}) ===`
                        });
                    }
                });
                
                this.socket.on('scraping_error', (data) => {
                    if (data.scraping_id === this.scrapingId) {
                        this.manualScraping = false;
                        this.manualSuccess = false;
                        this.manualResult = `Error: ${data.error}`;
                        this.scrapingLogs.push({
                            timestamp: data.timestamp,
                            log: `=== ERROR: ${data.error} ===`
                        });
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
            } catch (error) {
                console.error('Error refreshing status:', error);
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
                    this.scrapingId = data.data.scraping_id;
                    this.manualSuccess = true;
                    this.manualResult = data.message;
                    this.scrapingLogs.push({
                        timestamp: new Date().toISOString(),
                        log: `=== Iniciando scraping: ${this.manualConfig.operacion} ${this.manualConfig.tipo} ===`
                    });
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
        
        // Utility functions
        formatDate(dateStr) {
            if (!dateStr) return '-';
            
            const date = new Date(dateStr);
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
        }
    };
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Alpine.js will handle the initialization via x-data
    console.log('Scraper Control module loaded');
});
