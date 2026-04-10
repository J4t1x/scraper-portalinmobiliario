// Dashboard JavaScript - Chart.js Integration

console.log('Dashboard loaded');

// Global chart instances
let chartOperacion = null;
let chartTipo = null;
let chartComunas = null;

// Utility functions
function formatPrice(price) {
    if (!price) return 'N/A';
    return price;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('es-CL');
}

// Update clock
function updateTime() {
    const now = new Date();
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        timeElement.textContent = now.toLocaleString('es-CL');
    }
}

// Load statistics from API
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const result = await response.json();

        if (result.success) {
            const stats = result.data;
            updateKPIs(stats);
            createCharts(stats);
        } else {
            console.error('Error loading stats:', result.error);
            showErrorMessage('Error al cargar estadísticas');
        }
    } catch (error) {
        console.error('Error fetching stats:', error);
        showErrorMessage('Error de conexión al cargar estadísticas');
    }
}

// Update KPI cards
function updateKPIs(stats) {
    // Total properties
    const totalElement = document.getElementById('total-properties');
    if (totalElement) {
        totalElement.textContent = stats.total || 0;
    }

    // Files loaded
    const filesElement = document.getElementById('files-loaded');
    if (filesElement) {
        filesElement.textContent = stats.files_loaded || 0;
    }

    // Operation breakdown
    const operacionElement = document.getElementById('operacion-breakdown');
    if (operacionElement && stats.by_operacion) {
        const breakdown = Object.entries(stats.by_operacion)
            .map(([op, count]) => `${op}: ${count}`)
            .join(' | ');
        operacionElement.textContent = breakdown || '-';
    }

    // Type breakdown
    const tipoElement = document.getElementById('tipo-breakdown');
    if (tipoElement && stats.by_tipo) {
        const breakdown = Object.entries(stats.by_tipo)
            .map(([tipo, count]) => `${tipo}: ${count}`)
            .join(' | ');
        tipoElement.textContent = breakdown || '-';
    }
}

// Create all charts
function createCharts(stats) {
    createOperacionChart(stats.by_operacion);
    createTipoChart(stats.by_tipo);
    createComunasChart(stats.by_comuna);
}

// Operation distribution (pie chart)
function createOperacionChart(data) {
    const ctx = document.getElementById('chart-operacion');
    if (!ctx || !data) return;

    // Destroy existing chart
    if (chartOperacion) {
        chartOperacion.destroy();
    }

    const labels = Object.keys(data);
    const values = Object.values(data);

    chartOperacion = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    '#3B82F6', // blue
                    '#10B981', // green
                    '#F59E0B', // yellow
                    '#8B5CF6', // purple
                    '#EF4444'  // red
                ],
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Type distribution (bar chart)
function createTipoChart(data) {
    const ctx = document.getElementById('chart-tipo');
    if (!ctx || !data) return;

    // Destroy existing chart
    if (chartTipo) {
        chartTipo.destroy();
    }

    const labels = Object.keys(data);
    const values = Object.values(data);

    chartTipo = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Propiedades',
                data: values,
                backgroundColor: '#3B82F6',
                borderRadius: 4,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#E2E8F0'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// Top 10 comunas (horizontal bar chart)
function createComunasChart(data) {
    const ctx = document.getElementById('chart-comunas');
    if (!ctx || !data) return;

    // Destroy existing chart
    if (chartComunas) {
        chartComunas.destroy();
    }

    // Sort and get top 10
    const sortedData = Object.entries(data)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);

    const labels = sortedData.map(([comuna]) => comuna);
    const values = sortedData.map(([, count]) => count);

    chartComunas = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Propiedades',
                data: values,
                backgroundColor: '#10B981',
                borderRadius: 4,
                borderSkipped: false
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    beginAtZero: true,
                    grid: {
                        color: '#E2E8F0'
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// Show error message
function showErrorMessage(message) {
    console.error(message);
    // Could add a toast notification here
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initialized');

    // Start clock
    updateTime();
    setInterval(updateTime, 1000);

    // Load stats
    loadStats();
});
