/**
 * Modern SRM Seat Finder - JavaScript Application
 * Component-based architecture with modern UI interactions
 */

class ModernSeatFinder {
    constructor() {
        this.currentSessionId = null;
        this.progressInterval = null;
        this.isSearching = false;
        this.toast = new ToastManager();
        this.modal = new ModalManager();
        
        this.init();
    }

    init() {
        this.bindEventListeners();
        this.initializeComponents();
        this.setupSmoothScrolling();
        this.initializeAnimations();
    }

    bindEventListeners() {
        // Form submission
        const searchForm = document.getElementById('searchForm');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => this.handleSearch(e));
        }

        // Navigation
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => this.handleSmoothScroll(e));
        });

        // Button interactions
        this.bindButtonEvents();
        
        // Theme toggle (both desktop and mobile)
        document.querySelectorAll('.theme-toggle').forEach(toggle => {
            toggle.addEventListener('click', () => this.toggleTheme());
        });

        // Mobile menu toggle
        const mobileMenuButton = document.getElementById('mobileMenuButton');
        if (mobileMenuButton) {
            mobileMenuButton.addEventListener('click', () => this.toggleMobileMenu());
        }

        // Close mobile menu when clicking nav links
        document.querySelectorAll('.mobile-nav-link').forEach(link => {
            link.addEventListener('click', () => this.closeMobileMenu());
        });

        // Modal interactions
        this.bindModalEvents();
    }

    bindButtonEvents() {
        // Export button
        const exportButton = document.getElementById('exportButton');
        if (exportButton) {
            exportButton.addEventListener('click', () => this.handleExport());
        }

        // Search again button
        const searchAgainButton = document.getElementById('searchAgainButton');
        if (searchAgainButton) {
            searchAgainButton.addEventListener('click', () => this.handleSearchAgain());
        }

        // Try again button
        const tryAgainButton = document.getElementById('tryAgainButton');
        if (tryAgainButton) {
            tryAgainButton.addEventListener('click', () => this.handleTryAgain());
        }
    }

    bindModalEvents() {
        // Close modal
        const closeModal = document.getElementById('closeModal');
        if (closeModal) {
            closeModal.addEventListener('click', () => this.modal.hide());
        }

        // Click outside to close
        const modalOverlay = document.getElementById('exportModal');
        if (modalOverlay) {
            modalOverlay.addEventListener('click', (e) => {
                if (e.target === modalOverlay) {
                    this.modal.hide();
                }
            });
        }
    }

    initializeComponents() {
        // Initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    setupSmoothScrolling() {
        // Smooth scrolling is handled by CSS scroll-behavior: smooth
        // This is a fallback for browsers that don't support it
        if (!CSS.supports('scroll-behavior', 'smooth')) {
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function (e) {
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                });
            });
        }
    }

    initializeAnimations() {
        // Intersection Observer for animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-slide-up');
                }
            });
        }, observerOptions);

        // Observe elements with animation classes
        document.querySelectorAll('.animate-slide-up').forEach(el => {
            observer.observe(el);
        });
    }

    handleSmoothScroll(e) {
        e.preventDefault();
        const targetId = e.currentTarget.getAttribute('href');
        const targetElement = document.querySelector(targetId);
        
        if (targetElement) {
            const offsetTop = targetElement.offsetTop - 80; // Account for fixed navbar
            window.scrollTo({
                top: offsetTop,
                behavior: 'smooth'
            });
        }
    }

    async handleSearch(e) {
        e.preventDefault();
        
        if (this.isSearching) return;

        const formData = new FormData(e.target);
        const rollNumber = formData.get('rollNumber').trim();
        const examDate = formData.get('examDate');

        if (!this.validateForm(rollNumber, examDate)) {
            return;
        }

        this.isSearching = true;
        this.showSearching();
        
        try {
            // Clear any previous sessions
            await this.clearPreviousSessions();

            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    rollNumber: rollNumber,
                    date: examDate
                })
            });

            const data = await response.json();

            if (data.success) {
                this.currentSessionId = data.sessionId;
                console.log('Search started with session ID:', this.currentSessionId);
                
                // If results are already available (fast search), show them directly
                if (data.results && Array.isArray(data.results)) {
                    console.log('Search completed immediately with results:', data.results.length);
                    this.handleSearchComplete(data);
                } else {
                    // Start progress monitoring for longer searches
                    this.startProgressMonitoring();
                    this.toast.show('Search started successfully!', 'success');
                }
            } else {
                throw new Error(data.message || 'Search failed');
            }

        } catch (error) {
            console.error('Search error:', error);
            this.showError(error.message || 'Failed to start search. Please try again.');
            this.isSearching = false;
            this.resetSearchButton();
        }
    }

    validateForm(rollNumber, examDate) {
        if (!rollNumber) {
            this.toast.show('Please enter your roll number', 'error');
            return false;
        }

        if (rollNumber.length < 10) {
            this.toast.show('Please enter a valid roll number', 'error');
            return false;
        }

        if (!examDate) {
            this.toast.show('Please select an exam date', 'error');
            return false;
        }

        return true;
    }

    async clearPreviousSessions() {
        try {
            await fetch('/api/clear-sessions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
        } catch (error) {
            console.warn('Failed to clear previous sessions:', error);
        }
    }

    showSearching() {
        // Update search button to show loading state
        const searchButton = document.querySelector('.search-button');
        const buttonContent = searchButton?.querySelector('.button-content');
        const loadingSpinner = searchButton?.querySelector('.loading-spinner');
        
        if (searchButton) {
            searchButton.disabled = true;
        }
        
        if (buttonContent) {
            buttonContent.style.display = 'none';
        }
        
        if (loadingSpinner) {
            loadingSpinner.classList.remove('hidden');
        }
        
        // Reset progress bar before showing
        this.resetProgress();
        
        this.hideAllSections();
        const progressSection = document.getElementById('progressSection');
        if (progressSection) {
            progressSection.classList.remove('hidden');
            
            // Scroll to progress section
            setTimeout(() => {
                progressSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }, 100);
        }
    }

    startProgressMonitoring() {
        // Don't start if search is not active
        if (!this.isSearching || !this.currentSessionId) {
            console.log('Not starting progress monitoring - search not active');
            return;
        }

        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }

        console.log('Starting progress monitoring for session:', this.currentSessionId);
        this.progressInterval = setInterval(() => {
            this.checkProgress();
        }, 1000);
    }

    async checkProgress() {
        if (!this.currentSessionId) return;

        try {
            const response = await fetch(`/api/progress/${this.currentSessionId}`);
            
            if (!response.ok) {
                if (response.status === 404) {
                    console.log('Session not found yet, retrying...');
                    return; // Continue polling
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Log progress for debugging
            console.log('Progress update:', data);

            this.updateProgress(data);

            if (data.status === 'completed') {
                this.handleSearchComplete(data);
            } else if (data.status === 'error') {
                this.handleSearchError(data);
            }
            // Continue polling if status is 'searching'

        } catch (error) {
            console.error('Progress check error:', error);
            // Only show error after multiple failures
            if (!this.errorCount) this.errorCount = 0;
            this.errorCount++;
            
            if (this.errorCount >= 5) {
                this.handleSearchError({ message: 'Connection lost. Please refresh and try again.' });
            } else {
                console.log(`Retrying... (${this.errorCount}/5)`);
            }
        }
    }

    updateProgress(data) {
        const progressFill = document.getElementById('progressFill');
        const progressMessage = document.getElementById('progressMessage');
        const progressPercent = document.getElementById('progressPercent');

        if (progressFill) {
            const currentWidth = parseInt(progressFill.style.width) || 0;
            const targetWidth = Math.max(0, Math.min(100, data.progress || 0));
            
            // Only update if target is higher than current (prevent going backwards)
            if (targetWidth >= currentWidth) {
                progressFill.style.width = `${targetWidth}%`;
            }
        }

        if (progressMessage) {
            progressMessage.textContent = data.message || 'Searching...';
        }

        if (progressPercent) {
            const targetPercent = Math.max(0, Math.min(100, data.progress || 0));
            progressPercent.textContent = `${targetPercent}%`;
        }
    }

    handleSearchComplete(data) {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }

        this.isSearching = false;
        this.errorCount = 0; // Reset error count
        this.resetSearchButton();

        if (data.results && data.results.length > 0) {
            this.showResults(data.results);
            this.toast.show('Seat found successfully!', 'success');
        } else {
            this.showError('No exam seats found for the given details.');
        }
    }

    handleSearchError(data) {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }

        this.isSearching = false;
        this.errorCount = 0; // Reset error count
        this.resetSearchButton();
        this.showError(data.message || 'Search failed. Please try again.');
    }

    showResults(results) {
        this.hideAllSections();
        
        const resultsSection = document.getElementById('resultsSection');
        const resultsContainer = document.getElementById('resultsContainer');
        
        if (!resultsSection || !resultsContainer) return;

        resultsContainer.innerHTML = '';

        results.forEach((result, index) => {
            const resultCard = this.createResultCard(result, index);
            resultsContainer.appendChild(resultCard);
        });

        resultsSection.classList.remove('hidden');
        
        // Scroll to results
        setTimeout(() => {
            resultsSection.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }, 100);

        // Refresh icons
        if (typeof refreshIcons === 'function') {
            refreshIcons();
        }
    }

    createResultCard(result, index) {
        const card = document.createElement('div');
        card.className = 'result-card animate-slide-up';
        card.style.animationDelay = `${index * 0.1}s`;

        const sessionBadgeClass = result.session === 'FN' ? 'forenoon' : 'afternoon';
        
        card.innerHTML = `
            <div class="result-header">
                <h4 class="text-lg font-semibold text-white">
                    <i data-lucide="calendar" class="w-5 h-5 inline mr-2"></i>
                    Exam ${index + 1}
                </h4>
                <span class="result-badge ${sessionBadgeClass}">
                    ${result.session_name}
                </span>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-3">
                    <div class="result-detail">
                        <span class="result-label">Registration Number</span>
                        <span class="result-value font-mono">${result.registration_number}</span>
                    </div>
                    <div class="result-detail">
                        <span class="result-label">Date</span>
                        <span class="result-value">${result.date}</span>
                    </div>
                    <div class="result-detail">
                        <span class="result-label">Department</span>
                        <span class="result-value">${result.department}</span>
                    </div>
                </div>
                
                <div class="space-y-3">
                    <div class="result-detail">
                        <span class="result-label">Venue</span>
                        <span class="result-value text-green-400">${result.venue_name}</span>
                    </div>
                    <div class="result-detail">
                        <span class="result-label">Room</span>
                        <span class="result-value text-blue-400 text-lg font-bold">${result.room_number}</span>
                    </div>
                    <div class="result-detail">
                        <span class="result-label">Seat</span>
                        <span class="result-value highlight">${result.seat_number}</span>
                    </div>
                </div>
            </div>
        `;

        return card;
    }

    showError(message) {
        this.hideAllSections();
        
        const errorSection = document.getElementById('errorSection');
        const errorMessage = document.getElementById('errorMessage');
        
        if (errorSection) {
            errorSection.classList.remove('hidden');
        }
        
        if (errorMessage) {
            errorMessage.textContent = message;
        }

        this.toast.show(message, 'error');

        // Scroll to error section
        setTimeout(() => {
            if (errorSection) {
                errorSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }
        }, 100);
    }

    resetSearchButton() {
        // Reset search button to normal state
        const searchButton = document.querySelector('.search-button');
        const buttonContent = searchButton?.querySelector('.button-content');
        const loadingSpinner = searchButton?.querySelector('.loading-spinner');
        
        if (searchButton) {
            searchButton.disabled = false;
        }
        
        if (buttonContent) {
            buttonContent.style.display = 'flex';
        }
        
        if (loadingSpinner) {
            loadingSpinner.classList.add('hidden');
        }
    }

    hideAllSections() {
        const sections = ['progressSection', 'resultsSection', 'errorSection'];
        sections.forEach(sectionId => {
            const section = document.getElementById(sectionId);
            if (section) {
                section.classList.add('hidden');
            }
        });
    }

    resetProgress() {
        // Reset progress bar to initial state
        const progressFill = document.getElementById('progressFill');
        const progressMessage = document.getElementById('progressMessage');
        const progressPercent = document.getElementById('progressPercent');

        if (progressFill) {
            progressFill.style.width = '0%';
        }

        if (progressMessage) {
            progressMessage.textContent = 'Initializing search...';
        }

        if (progressPercent) {
            progressPercent.textContent = '0%';
        }
    }

    async handleExport() {
        if (!this.currentSessionId) {
            this.toast.show('No results to export', 'error');
            return;
        }

        try {
            const response = await fetch(`/api/export/${this.currentSessionId}/options`);
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            this.showExportModal(data.available_formats);

        } catch (error) {
            console.error('Export error:', error);
            this.toast.show(error.message || 'Failed to load export options', 'error');
        }
    }

    showExportModal(exportFormats) {
        const exportOptions = document.getElementById('exportOptions');
        if (!exportOptions) return;

        exportOptions.innerHTML = '';

        exportFormats.forEach(format => {
            const option = document.createElement('div');
            option.className = 'export-option';
            option.addEventListener('click', () => this.handleExportOption(format));

            option.innerHTML = `
                <div class="export-icon bg-gradient-to-br from-blue-500 to-purple-500">
                    ${format.icon}
                </div>
                <div class="export-details flex-1">
                    <h4>${format.name}</h4>
                    <p>${format.description}</p>
                </div>
                <i data-lucide="chevron-right" class="w-5 h-5 text-slate-400"></i>
            `;

            exportOptions.appendChild(option);
        });

        this.modal.show();
        
        // Refresh icons
        if (typeof refreshIcons === 'function') {
            refreshIcons();
        }
    }

    handleExportOption(format) {
        this.modal.hide();

        if (format.external) {
            // Open external URL (WhatsApp)
            window.open(format.url, '_blank');
            this.toast.show('Opening WhatsApp...', 'success');
        } else {
            // Download file
            window.location.href = format.url;
            this.toast.show('Download started...', 'success');
        }
    }

    handleSearchAgain() {
        // Clear current session
        this.currentSessionId = null;
        this.isSearching = false;
        this.errorCount = 0; // Reset error count
        
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }

        // Reset search button
        this.resetSearchButton();

        // Reset progress bar
        this.resetProgress();

        // Hide all sections
        this.hideAllSections();

        // Clear form
        const form = document.getElementById('searchForm');
        if (form) {
            form.reset();
        }

        // Scroll to search section
        const searchSection = document.getElementById('search');
        if (searchSection) {
            searchSection.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }

        this.toast.show('Ready for new search', 'success');
    }

    handleTryAgain() {
        this.handleSearchAgain();
    }

    toggleTheme() {
        const html = document.documentElement;
        const isDark = html.classList.contains('dark');
        
        if (isDark) {
            html.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        } else {
            html.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        }

        this.toast.show(`Switched to ${isDark ? 'light' : 'dark'} theme`, 'success');
    }

    toggleMobileMenu() {
        const mobileMenu = document.getElementById('mobileMenu');
        const mobileMenuButton = document.getElementById('mobileMenuButton');
        const menuOpenIcon = mobileMenuButton?.querySelector('.mobile-menu-open');
        const menuCloseIcon = mobileMenuButton?.querySelector('.mobile-menu-close');

        if (!mobileMenu) return;

        const isHidden = mobileMenu.classList.contains('hidden');

        if (isHidden) {
            // Show menu
            mobileMenu.classList.remove('hidden');
            menuOpenIcon?.classList.add('hidden');
            menuCloseIcon?.classList.remove('hidden');
        } else {
            // Hide menu
            mobileMenu.classList.add('hidden');
            menuOpenIcon?.classList.remove('hidden');
            menuCloseIcon?.classList.add('hidden');
        }

        // Refresh icons
        if (typeof refreshIcons === 'function') {
            refreshIcons();
        }
    }

    closeMobileMenu() {
        const mobileMenu = document.getElementById('mobileMenu');
        const mobileMenuButton = document.getElementById('mobileMenuButton');
        const menuOpenIcon = mobileMenuButton?.querySelector('.mobile-menu-open');
        const menuCloseIcon = mobileMenuButton?.querySelector('.mobile-menu-close');

        if (!mobileMenu) return;

        mobileMenu.classList.add('hidden');
        menuOpenIcon?.classList.remove('hidden');
        menuCloseIcon?.classList.add('hidden');

        // Refresh icons
        if (typeof refreshIcons === 'function') {
            refreshIcons();
        }
    }
}

// Toast Manager Class
class ToastManager {
    constructor() {
        this.toast = document.getElementById('toast');
        this.toastIcon = this.toast?.querySelector('.toast-icon');
        this.toastMessage = this.toast?.querySelector('.toast-message');
        this.hideTimeout = null;
    }

    show(message, type = 'success') {
        if (!this.toast) return;

        // Clear any existing timeout
        if (this.hideTimeout) {
            clearTimeout(this.hideTimeout);
        }

        // Update content
        if (this.toastMessage) {
            this.toastMessage.textContent = message;
        }

        // Update icon based on type
        if (this.toastIcon) {
            try {
                // Remove all type classes first
                this.toastIcon.classList.remove('toast-success', 'toast-error', 'toast-warning', 'toast-info');
                
                switch (type) {
                    case 'success':
                        this.toastIcon.setAttribute('data-lucide', 'check-circle');
                        this.toastIcon.classList.add('toast-success');
                        break;
                    case 'error':
                        this.toastIcon.setAttribute('data-lucide', 'alert-circle');
                        this.toastIcon.classList.add('toast-error');
                        break;
                    case 'warning':
                        this.toastIcon.setAttribute('data-lucide', 'alert-triangle');
                        this.toastIcon.classList.add('toast-warning');
                        break;
                    default:
                        this.toastIcon.setAttribute('data-lucide', 'info');
                        this.toastIcon.classList.add('toast-info');
                }
            } catch (error) {
                console.warn('Error updating toast icon:', error);
                // Fallback: just set the data-lucide attribute
                switch (type) {
                    case 'success':
                        this.toastIcon.setAttribute('data-lucide', 'check-circle');
                        break;
                    case 'error':
                        this.toastIcon.setAttribute('data-lucide', 'alert-circle');
                        break;
                    case 'warning':
                        this.toastIcon.setAttribute('data-lucide', 'alert-triangle');
                        break;
                    default:
                        this.toastIcon.setAttribute('data-lucide', 'info');
                }
            }
        }

        // Show toast
        this.toast.classList.add('show');
        this.toast.classList.remove('hidden');

        // Refresh icons
        if (typeof refreshIcons === 'function') {
            refreshIcons();
        }

        // Auto hide after 2 seconds
        this.hideTimeout = setTimeout(() => {
            this.hide();
        }, 2000);
    }

    hide() {
        if (this.toast) {
            this.toast.classList.remove('show');
            setTimeout(() => {
                this.toast.classList.add('hidden');
            }, 300);
        }

        if (this.hideTimeout) {
            clearTimeout(this.hideTimeout);
            this.hideTimeout = null;
        }
    }
}

// Modal Manager Class
class ModalManager {
    constructor() {
        this.modal = document.getElementById('exportModal');
    }

    show() {
        if (this.modal) {
            this.modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    }

    hide() {
        if (this.modal) {
            this.modal.classList.add('hidden');
            document.body.style.overflow = '';
        }
    }
}

// Global functions for navigation
function scrollToSearch() {
    const searchSection = document.getElementById('search');
    if (searchSection) {
        searchSection.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

function scrollToAbout() {
    const aboutSection = document.getElementById('about');
    if (aboutSection) {
        aboutSection.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme from localStorage
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.documentElement.classList.remove('dark');
    } else {
        document.documentElement.classList.add('dark');
    }

    // Initialize the main application
    window.seatFinder = new ModernSeatFinder();
    
    console.log('🚀 Modern SRM Seat Finder initialized successfully!');
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden - pause any intensive operations
        if (window.seatFinder && window.seatFinder.progressInterval) {
            clearInterval(window.seatFinder.progressInterval);
        }
    } else {
        // Page is visible - resume operations
        if (window.seatFinder && window.seatFinder.currentSessionId && window.seatFinder.isSearching) {
            window.seatFinder.startProgressMonitoring();
        }
    }
});

// Handle beforeunload for cleanup
window.addEventListener('beforeunload', () => {
    if (window.seatFinder && window.seatFinder.progressInterval) {
        clearInterval(window.seatFinder.progressInterval);
    }
}); 