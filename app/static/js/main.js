// Main JavaScript for Salesforce Health Check Dashboard

document.addEventListener('DOMContentLoaded', function() {
    // Initialize collapsible AI insights and health summary
    initCollapsibleComponents();
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            delay: { show: 50, hide: 50 },
            animation: true
        });
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Set active nav item based on current path
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (currentPath === href) {
            link.classList.add('active');
        }
    });
    
    // Add animation effects for card appearance
    const cards = document.querySelectorAll('.card');
    if (cards.length > 0) {
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(10px)';
            setTimeout(() => {
                card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, 100 + (index * 50)); // Staggered animation
        });
    }
    
    // Add click effects for buttons
    const buttons = document.querySelectorAll('.btn');
    if (buttons.length > 0) {
        buttons.forEach(button => {
            button.addEventListener('mousedown', function() {
                this.style.transform = 'scale(0.98)';
            });
            
            button.addEventListener('mouseup', function() {
                this.style.transform = 'scale(1)';
            });
            
            button.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1)';
            });
        });
    }
    
    // Enhance table rows with hover effects
    const tableRows = document.querySelectorAll('tbody tr');
    if (tableRows.length > 0) {
        tableRows.forEach(row => {
            row.addEventListener('mouseenter', function() {
                this.style.transition = 'background-color 0.2s ease';
            });
        });
    }
    
    // Handle API errors with better UX
    window.handleApiError = function(error, errorMessage, targetElement = null) {
        console.error(error);
        
        if (targetElement) {
            // Show inline error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger mt-3 mb-3 error-message';
            errorDiv.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="bi bi-exclamation-circle me-2"></i>
                    <div>${errorMessage || 'An error occurred. Please try again.'}</div>
                </div>
                <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            targetElement.appendChild(errorDiv);
            
            // Automatically remove after 8 seconds
            setTimeout(() => {
                if (errorDiv.parentNode) {
                    errorDiv.classList.add('fade-out');
                    setTimeout(() => {
                        if (errorDiv.parentNode) {
                            errorDiv.parentNode.removeChild(errorDiv);
                        }
                    }, 500);
                }
            }, 8000);
        } else {
            // Show toast notification
            const toastContainer = document.getElementById('toast-container');
            if (!toastContainer) {
                const container = document.createElement('div');
                container.id = 'toast-container';
                container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
                document.body.appendChild(container);
            }
            
            const toastId = 'error-toast-' + Date.now();
            const toastHtml = `
                <div id="${toastId}" class="toast align-items-center text-white bg-danger border-0" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="d-flex">
                        <div class="toast-body">
                            <i class="bi bi-exclamation-circle me-2"></i>
                            ${errorMessage || 'An error occurred. Please try again.'}
                        </div>
                        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                    </div>
                </div>
            `;
            
            document.getElementById('toast-container').innerHTML += toastHtml;
            const toastElement = document.getElementById(toastId);
            const toast = new bootstrap.Toast(toastElement, {
                autohide: true,
                delay: 5000
            });
            toast.show();
        }
    };
    
    // Format date strings
    window.formatDate = function(dateString) {
        const date = new Date(dateString);
        const options = { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit'
        };
        return date.toLocaleDateString(undefined, options);
    };
    
    // Format relative time
    window.formatRelativeTime = function(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        
        if (diffInSeconds < 60) {
            return 'just now';
        }
        
        const diffInMinutes = Math.floor(diffInSeconds / 60);
        if (diffInMinutes < 60) {
            return `${diffInMinutes}m ago`;
        }
        
        const diffInHours = Math.floor(diffInMinutes / 60);
        if (diffInHours < 24) {
            return `${diffInHours}h ago`;
        }
        
        const diffInDays = Math.floor(diffInHours / 24);
        if (diffInDays < 30) {
            return `${diffInDays}d ago`;
        }
        
        const options = { month: 'short', day: 'numeric' };
        return date.toLocaleDateString(undefined, options);
    };
    
    // Initialize collapsible components (AI Insights and Health Summary)
    function initCollapsibleComponents() {
        // Expand/collapse functionality for AI insights
        document.querySelectorAll('.expand-insight').forEach(button => {
            button.addEventListener('click', function() {
                const insightId = this.getAttribute('data-insight');
                const detailSection = document.getElementById(insightId);
                const icon = this.querySelector('i');
                
                if (detailSection.style.display === 'none' || !detailSection.style.display) {
                    // Expand the section
                    detailSection.style.display = 'block';
                    detailSection.style.opacity = '0';
                    icon.classList.remove('bi-chevron-down');
                    icon.classList.add('bi-chevron-up');
                    
                    // Animate the expansion
                    setTimeout(() => {
                        detailSection.style.transition = 'opacity 0.3s ease';
                        detailSection.style.opacity = '1';
                    }, 10);
                } else {
                    // Collapse the section with animation
                    detailSection.style.transition = 'opacity 0.2s ease';
                    detailSection.style.opacity = '0';
                    icon.classList.remove('bi-chevron-up');
                    icon.classList.add('bi-chevron-down');
                    
                    setTimeout(() => {
                        detailSection.style.display = 'none';
                    }, 200);
                }
            });
        });
        
        // Toggle health summary expand/collapse
        const toggleHealthSummary = document.getElementById('toggle-health-summary');
        const healthSummaryDetail = document.getElementById('health-summary-detail');
        
        if (toggleHealthSummary && healthSummaryDetail) {
            toggleHealthSummary.addEventListener('click', function() {
                const icon = this.querySelector('i');
                
                if (healthSummaryDetail.style.display === 'none' || !healthSummaryDetail.style.display) {
                    // Expand health summary
                    healthSummaryDetail.style.display = 'block';
                    healthSummaryDetail.style.opacity = '0';
                    icon.classList.remove('bi-chevron-down');
                    icon.classList.add('bi-chevron-up');
                    
                    // Animate the expansion
                    setTimeout(() => {
                        healthSummaryDetail.style.transition = 'opacity 0.3s ease';
                        healthSummaryDetail.style.opacity = '1';
                    }, 10);
                } else {
                    // Collapse health summary with animation
                    healthSummaryDetail.style.transition = 'opacity 0.2s ease';
                    healthSummaryDetail.style.opacity = '0';
                    icon.classList.remove('bi-chevron-up');
                    icon.classList.add('bi-chevron-down');
                    
                    setTimeout(() => {
                        healthSummaryDetail.style.display = 'none';
                    }, 200);
                }
            });
        }
    }
    
    // Initialize any category filter dropdowns
    const categoryFilters = document.querySelectorAll('.category-filter');
    if (categoryFilters.length > 0) {
        categoryFilters.forEach(filter => {
            filter.addEventListener('change', function() {
                const selectedCategory = this.value;
                const tableRows = document.querySelectorAll('tbody tr');
                
                if (selectedCategory === 'all') {
                    tableRows.forEach(row => {
                        row.style.display = '';
                    });
                } else {
                    tableRows.forEach(row => {
                        const rowCategory = row.dataset.category;
                        if (rowCategory === selectedCategory) {
                            row.style.display = '';
                        } else {
                            row.style.display = 'none';
                        }
                    });
                }
            });
        });
    }
});