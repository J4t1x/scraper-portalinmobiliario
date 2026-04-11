// Dashboard JavaScript - Chart.js Integration

console.log('Dashboard loaded');

// Global chart instances
let chartOperacion = null;
let chartTipo = null;
let chartComunas = null;
let chartPriceRanges = null;
let chartTemporal = null;
let chartPublishers = null;
let chartCompleteness = null;

// Utility functions
function formatPrice(price) {
    if (!price) return 'N/A';
    if (price >= 1000000) {
        return `$${(price / 1000000).toFixed(1)}M`;
    }
    return `$${price.toLocaleString('es-CL')}`;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-CL');
}

function formatPercentage(value) {
    if (value === null || value === undefined) return '0%';
    return `${value.toFixed(1)}%`;
}

// Update clock
function updateTime() {
    const now = new Date();
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        timeElement.textContent = now.toLocaleString('es-CL');
    }
}

// Load advanced statistics from API
async function loadStats() {
    try {
        const response = await fetch('/api/advanced-stats');
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
    const basic = stats.basic || {};
    const prices = stats.prices || {};
    const completeness = stats.completeness || {};
    const temporal = stats.temporal || {};
    const publishers = stats.publishers || {};

    // Total properties
    const totalElement = document.getElementById('total-properties');
    if (totalElement) {
        totalElement.textContent = basic.total || 0;
    }

    // Average price
    const avgPriceElement = document.getElementById('avg-price');
    const priceRangeElement = document.getElementById('price-range');
    if (avgPriceElement && prices.avg) {
        avgPriceElement.textContent = formatPrice(prices.avg);
    }
    if (priceRangeElement && prices.min && prices.max) {
        priceRangeElement.textContent = `Rango: ${formatPrice(prices.min)} - ${formatPrice(prices.max)}`;
    }

    // Completeness
    const completenessElement = document.getElementById('completeness-overall');
    const completenessBar = document.getElementById('completeness-bar');
    if (completenessElement && completeness.overall !== undefined) {
        completenessElement.textContent = formatPercentage(completeness.overall);
    }
    if (completenessBar && completeness.overall !== undefined) {
        completenessBar.style.width = `${completeness.overall}%`;
    }

    // Files loaded
    const filesElement = document.getElementById('files-loaded');
    const latestDateElement = document.getElementById('latest-date');
    if (filesElement) {
        filesElement.textContent = basic.files_loaded || 0;
    }
    if (latestDateElement && temporal.latest_date) {
        latestDateElement.textContent = `Último: ${formatDate(temporal.latest_date)}`;
    }

    // With images
    const withImagesElement = document.getElementById('with-images');
    const imagesPercentageElement = document.getElementById('images-percentage');
    if (withImagesElement && completeness.with_images !== undefined) {
        withImagesElement.textContent = completeness.with_images;
    }
    if (imagesPercentageElement && completeness.fields && completeness.fields.imagenes !== undefined) {
        imagesPercentageElement.textContent = formatPercentage(completeness.fields.imagenes);
    }

    // With description
    const withDescElement = document.getElementById('with-description');
    const descPercentageElement = document.getElementById('description-percentage');
    if (withDescElement && completeness.with_description !== undefined) {
        withDescElement.textContent = completeness.with_description;
    }
    if (descPercentageElement && completeness.fields && completeness.fields.descripcion !== undefined) {
        descPercentageElement.textContent = formatPercentage(completeness.fields.descripcion);
    }

    // With coordinates
    const withCoordsElement = document.getElementById('with-coordinates');
    const coordsPercentageElement = document.getElementById('coordinates-percentage');
    if (withCoordsElement && completeness.with_coordinates !== undefined) {
        withCoordsElement.textContent = completeness.with_coordinates;
    }
    if (coordsPercentageElement && completeness.fields && completeness.fields.coordenadas !== undefined) {
        coordsPercentageElement.textContent = formatPercentage(completeness.fields.coordenadas);
    }

    // Publishers
    const publishersElement = document.getElementById('total-publishers');
    const publishersInfoElement = document.getElementById('publishers-info');
    if (publishersElement && publishers.total_publishers !== undefined) {
        publishersElement.textContent = publishers.total_publishers;
    }
    if (publishersInfoElement && publishers.total_with_publisher !== undefined) {
        publishersInfoElement.textContent = `${publishers.total_with_publisher} propiedades`;
    }
}

// Create all charts
function createCharts(stats) {
    createOperacionChart(stats.basic?.by_operacion);
    createTipoChart(stats.basic?.by_tipo);
    createComunasChart(stats.by_comuna);
    createPriceRangesChart(stats.price_ranges);
    createTemporalChart(stats.temporal?.by_date);
    createPublishersChart(stats.publishers?.top);
    createCompletenessChart(stats.completeness?.fields);
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

// Price ranges distribution (bar chart)
function createPriceRangesChart(data) {
    const ctx = document.getElementById('chart-price-ranges');
    if (!ctx || !data) return;

    if (chartPriceRanges) {
        chartPriceRanges.destroy();
    }

    const labels = Object.keys(data);
    const values = Object.values(data);

    chartPriceRanges = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Propiedades',
                data: values,
                backgroundColor: '#F59E0B',
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

// Temporal distribution (line chart)
function createTemporalChart(data) {
    const ctx = document.getElementById('chart-temporal');
    if (!ctx || !data) return;

    if (chartTemporal) {
        chartTemporal.destroy();
    }

    // Get last 30 dates
    const entries = Object.entries(data);
    const last30 = entries.slice(-30);
    const labels = last30.map(([date]) => formatDate(date));
    const values = last30.map(([, count]) => count);

    chartTemporal = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Propiedades Scrapeadas',
                data: values,
                borderColor: '#3B82F6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 5
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
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
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

// Top publishers (horizontal bar chart)
function createPublishersChart(data) {
    const ctx = document.getElementById('chart-publishers');
    if (!ctx || !data) return;

    if (chartPublishers) {
        chartPublishers.destroy();
    }

    const labels = Object.keys(data);
    const values = Object.values(data);

    chartPublishers = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Propiedades',
                data: values,
                backgroundColor: '#EF4444',
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

// Completeness fields (horizontal bar chart)
function createCompletenessChart(data) {
    const ctx = document.getElementById('chart-completeness');
    if (!ctx || !data) return;

    if (chartCompleteness) {
        chartCompleteness.destroy();
    }

    const labels = Object.keys(data).map(field => {
        const fieldNames = {
            'titulo': 'Título',
            'precio': 'Precio',
            'ubicacion': 'Ubicación',
            'descripcion': 'Descripción',
            'features': 'Características',
            'imagenes': 'Imágenes',
            'publisher': 'Publicador',
            'coordenadas': 'Coordenadas'
        };
        return fieldNames[field] || field;
    });
    const values = Object.values(data);

    chartCompleteness = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Completitud (%)',
                data: values,
                backgroundColor: '#8B5CF6',
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
                    max: 100,
                    grid: {
                        color: '#E2E8F0'
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
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
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.parsed.x.toFixed(1)}%`;
                        }
                    }
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
