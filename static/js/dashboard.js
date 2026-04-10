// Dashboard main JavaScript

console.log('Dashboard loaded');

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

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initialized');
});
