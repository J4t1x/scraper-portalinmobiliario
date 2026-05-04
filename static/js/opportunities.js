function opportunitiesApp() {
    return {
        featured: null,
        topList: [],
        scoreSummary: {},
        marketStats: {},
        communes: [],
        alerts: [],
        meta: { total: 0, last_updated: null },
        loading: false,
        pipelineRunning: false,
        activeTipo: null,
        activaComuna: null,
        tipoOptions: [
            { value: null,        label: 'Todos' },
            { value: 'excelente', label: 'Excelente' },
            { value: 'muy_buena', label: 'Muy buena' },
            { value: 'buena',     label: 'Buena' },
            { value: 'moderada',  label: 'Moderada' },
        ],

        init() {
            this.loadOpportunities();
            setInterval(() => this.loadOpportunities(), 5 * 60 * 1000);
        },

        buildUrl() {
            const params = new URLSearchParams({ limit: 20 });
            if (this.activeTipo)   params.set('tipo',   this.activeTipo);
            if (this.activaComuna) params.set('comuna', this.activaComuna);
            return `/api/daily-opportunities?${params.toString()}`;
        },

        async loadOpportunities() {
            this.loading = true;
            try {
                const response = await fetch(this.buildUrl());
                const result = await response.json();

                if (result.success) {
                    const d = result.data;
                    this.featured      = d.featured      || null;
                    this.topList       = d.top_list       || [];
                    this.scoreSummary  = d.score_summary  || {};
                    this.marketStats   = d.market_stats   || {};
                    this.communes      = d.communes        || [];
                    this.alerts        = d.alerts          || [];
                    this.meta          = d.meta            || { total: 0, last_updated: null };
                } else {
                    console.error('Error loading opportunities:', result.error);
                    this.alerts = [{ type: 'warning', message: result.error || 'Error al cargar oportunidades' }];
                }
            } catch (err) {
                console.error('Error fetching opportunities:', err);
                this.alerts = [{ type: 'warning', message: 'Error de conexión al servidor' }];
            } finally {
                this.loading = false;
                this.$nextTick(() => {
                    if (typeof lucide !== 'undefined') lucide.createIcons();
                });
            }
        },

        async runPipeline() {
            if (this.pipelineRunning) return;
            this.pipelineRunning = true;
            try {
                const response = await fetch('/api/daily-opportunities/run-pipeline', { method: 'POST' });
                const result = await response.json();
                if (result.success) {
                    await this.loadOpportunities();
                } else {
                    alert('Error al correr el análisis: ' + (result.error || 'desconocido'));
                }
            } catch (err) {
                alert('Error de conexión al ejecutar el pipeline');
            } finally {
                this.pipelineRunning = false;
            }
        },

        setTipoFilter(value) {
            this.activeTipo = value;
            this.loadOpportunities();
        },

        setComunaFilter(value) {
            this.activaComuna = value === this.activaComuna ? null : value;
            this.loadOpportunities();
        },

        tipoLabel(tipo) {
            const labels = {
                excelente:  'Excelente',
                muy_buena:  'Muy buena',
                buena:      'Buena',
                moderada:   'Moderada',
            };
            return labels[tipo] || tipo || '-';
        },

        scoreColor(score) {
            if (score >= 60) return 'font-bold text-emerald-600';
            if (score >= 40) return 'font-bold text-blue-600';
            if (score >= 25) return 'font-bold text-amber-600';
            return 'font-bold text-slate-500';
        },

        alertClass(type) {
            const map = {
                highlight:  'bg-amber-50 border-amber-200',
                new:        'bg-emerald-50 border-emerald-200',
                commune:    'bg-blue-50 border-blue-200',
                price_drop: 'bg-red-50 border-red-200',
                warning:    'bg-slate-50 border-slate-200',
            };
            return map[type] || 'bg-slate-50 border-slate-200';
        },

        alertIcon(type) {
            const map = {
                highlight:  'star',
                new:        'sparkles',
                commune:    'map-pin',
                price_drop: 'trending-down',
                warning:    'alert-circle',
            };
            return map[type] || 'info';
        },

        formatPrice(price) {
            if (!price) return '-';
            return new Intl.NumberFormat('es-CL', {
                style: 'currency',
                currency: 'CLP',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
            }).format(price);
        },

        formatDate(isoString) {
            if (!isoString) return '';
            try {
                return new Date(isoString).toLocaleString('es-CL', {
                    dateStyle: 'short', timeStyle: 'short'
                });
            } catch { return isoString; }
        },

        viewDetail(propertyId) {
            if (propertyId) window.location.href = `/property/${propertyId}`;
        },

        openPublication(property) {
            if (property && property.url) window.open(property.url, '_blank');
        },
    };
}
