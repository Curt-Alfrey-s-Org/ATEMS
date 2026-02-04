/**
 * ATEMS Tooltip System
 * Provides contextual help throughout the application
 */

// Tooltip data for different pages
const TOOLTIPS = {
    dashboard: {
        'total-tools': 'Total number of tools in the system across all locations and categories',
        'in-stock': 'Tools currently available for checkout',
        'checked-out': 'Tools currently checked out to users',
        'calibration-overdue': 'Tools that require calibration attention',
        'recent-activity': 'Latest check-in and check-out events across all tools',
    },
    checkinout: {
        'username': 'Enter your username as registered in the system',
        'badge-id': 'Scan or enter your employee badge ID',
        'tool-id': 'Scan or enter the tool ID number (e.g., CONS-HAM-001)',
        'job-id': 'Optional: Enter the job or project ID for tracking',
        'condition': 'Optional: Report the tool condition (Good, Fair, or Damaged)',
        'submit-btn': 'Submit to check out (if tool is available) or check in (if you have it checked out)',
    },
    selftest: {
        'run-tests': 'Run a comprehensive system health check including database, API, and internal modules',
        'test-status': 'Current system health status based on the most recent test run',
        'test-results': 'Detailed results from each test module with pass/fail status',
    },
};

// Initialize tooltips on page load
document.addEventListener('DOMContentLoaded', function() {
    initTooltips();
});

function initTooltips() {
    // Detect current page
    const path = window.location.pathname;
    let page = 'dashboard';
    if (path.includes('checkinout')) page = 'checkinout';
    else if (path.includes('selftest')) page = 'selftest';
    
    const pageTooltips = TOOLTIPS[page] || {};
    
    // Add tooltips to elements with data-tooltip attribute
    Object.keys(pageTooltips).forEach(key => {
        const elements = document.querySelectorAll(`[data-tooltip="${key}"]`);
        elements.forEach(el => {
            addTooltip(el, pageTooltips[key]);
        });
    });
}

function addTooltip(element, text) {
    // Add info icon if not present
    if (!element.querySelector('.tooltip-icon')) {
        const icon = document.createElement('span');
        icon.className = 'tooltip-icon ml-2 inline-flex items-center justify-center w-5 h-5 text-xs rounded-full bg-blue-500/20 text-blue-400 cursor-help';
        icon.innerHTML = '?';
        icon.setAttribute('title', text);
        
        // Position based on element type
        if (element.tagName === 'LABEL') {
            element.appendChild(icon);
        } else {
            element.style.position = 'relative';
            element.appendChild(icon);
        }
        
        // Create tooltip popup
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip-popup hidden absolute z-50 px-3 py-2 text-sm text-white bg-slate-800 rounded-lg shadow-lg border border-slate-700 max-w-xs';
        tooltip.style.bottom = '100%';
        tooltip.style.left = '50%';
        tooltip.style.transform = 'translateX(-50%) translateY(-8px)';
        tooltip.style.whiteSpace = 'normal';
        tooltip.textContent = text;
        
        // Arrow
        const arrow = document.createElement('div');
        arrow.className = 'absolute w-2 h-2 bg-slate-800 border-r border-b border-slate-700 transform rotate-45';
        arrow.style.bottom = '-4px';
        arrow.style.left = '50%';
        arrow.style.transform = 'translateX(-50%) rotate(45deg)';
        tooltip.appendChild(arrow);
        
        icon.appendChild(tooltip);
        
        // Show/hide on hover
        icon.addEventListener('mouseenter', () => {
            tooltip.classList.remove('hidden');
        });
        icon.addEventListener('mouseleave', () => {
            tooltip.classList.add('hidden');
        });
    }
}

// Export for manual use
window.ATEMS = window.ATEMS || {};
window.ATEMS.addTooltip = addTooltip;
