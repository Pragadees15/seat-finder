// SRM Exam Seat Finder - JavaScript Application
class SeatFinderApp {
    constructor() {
        this.currentSessionId = null;
        this.progressInterval = null;
        this.appVersion = Date.now(); // Cache busting version
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupScrollEffects();
        this.setupAnimations();
        this.setupFormValidation();
        this.setupGlobalErrorHandling();
    }
    
    setupGlobalErrorHandling() {
        // Catch unhandled JavaScript errors
        window.addEventListener('error', (event) => {
            console.error('🚨 Unhandled JavaScript error:', event.error);
            console.error('Error details:', {
                message: event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        });
        
        // Catch unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            console.error('🚨 Unhandled promise rejection:', event.reason);
            event.preventDefault(); // Prevent default browser error handling
        });
    }

    setupEventListeners() {
        // Form submission
        const searchForm = document.getElementById('searchForm');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => this.handleSearch(e));
        }

        // Navigation smooth scrolling
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => this.handleNavigation(e));
        });

        // Button event listeners
        const exportButton = document.getElementById('exportButton');
        if (exportButton) {
            exportButton.addEventListener('click', () => this.exportResults());
        }

        const searchAgainButton = document.getElementById('searchAgainButton');
        if (searchAgainButton) {
            searchAgainButton.addEventListener('click', () => this.resetSearch());
        }

        const tryAgainButton = document.getElementById('tryAgainButton');
        if (tryAgainButton) {
            tryAgainButton.addEventListener('click', () => this.resetSearch());
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));

        // Window resize handler
        window.addEventListener('resize', () => this.handleResize());
    }

    setupScrollEffects() {
        // Navbar scroll effect
        window.addEventListener('scroll', () => {
            const navbar = document.querySelector('.navbar');
            if (window.scrollY > 100) {
                navbar.style.background = 'rgba(255, 255, 255, 0.98)';
                navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.1)';
            } else {
                navbar.style.background = 'rgba(255, 255, 255, 0.95)';
                navbar.style.boxShadow = 'none';
            }
        });

        // Intersection Observer for animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                }
            });
        }, observerOptions);

        // Observe elements for animation
        document.querySelectorAll('.feature-item, .search-card, .section-header').forEach(el => {
            observer.observe(el);
        });
    }

    setupAnimations() {
        // Floating card animation enhancement
        const floatingCard = document.querySelector('.floating-card');
        if (floatingCard) {
            let mouseX = 0;
            let mouseY = 0;

            document.addEventListener('mousemove', (e) => {
                mouseX = (e.clientX / window.innerWidth) * 2 - 1;
                mouseY = (e.clientY / window.innerHeight) * 2 - 1;

                const translateX = mouseX * 10;
                const translateY = mouseY * 10;
                const rotateX = mouseY * 5;
                const rotateY = mouseX * 5;

                floatingCard.style.transform = `
                    translateX(${translateX}px) 
                    translateY(${translateY}px) 
                    rotateX(${rotateX}deg) 
                    rotateY(${rotateY}deg)
                `;
            });
        }

        // Parallax effect for hero background
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const parallaxElements = document.querySelectorAll('.hero::before');
            parallaxElements.forEach(el => {
                el.style.transform = `translateY(${scrolled * 0.5}px)`;
            });
        });
    }

    setupFormValidation() {
        const rollNumberInput = document.getElementById('rollNumber');
        const examDateInput = document.getElementById('examDate');

        if (rollNumberInput) {
            rollNumberInput.addEventListener('input', (e) => {
                this.validateRollNumber(e.target);
            });
        }

        if (examDateInput) {
            examDateInput.addEventListener('change', (e) => {
                this.validateDate(e.target);
            });
        }
    }

    validateRollNumber(input) {
        const value = input.value.trim();
        const isValid = value.length >= 10 && /^[A-Z]+\d+$/.test(value);
        
        this.updateInputValidation(input, isValid);
        return isValid;
    }

    validateDate(input) {
        const value = input.value.trim();
        
        // HTML5 date input uses YYYY-MM-DD format
        // If there's a value, it's automatically valid (HTML5 handles validation)
        if (value) {
            this.updateInputValidation(input, true);
            return true;
        } else {
            this.updateInputValidation(input, false);
            return false;
        }
    }

    updateInputValidation(input, isValid) {
        const wrapper = input.parentElement;
        
        if (isValid) {
            wrapper.classList.remove('error');
            wrapper.classList.add('success');
        } else {
            wrapper.classList.remove('success');
            wrapper.classList.add('error');
        }
    }

    async handleSearch(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const rollNumber = formData.get('rollNumber').trim();
        const examDate = formData.get('examDate').trim();

        // Validate inputs
        if (!this.validateRollNumber(document.getElementById('rollNumber')) ||
            !this.validateDate(document.getElementById('examDate'))) {
            this.showToast('Please enter valid roll number and date', 'error');
            return;
        }

        // Show loading state
        this.setLoadingState(true);
        this.hideAllSections();

        try {
            // Start search
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
                this.showToast('Search started! Finding your exam details...', 'success');
                
                // Start direct result polling without progress bar
                this.startDirectResultPolling();
            } else {
                throw new Error(data.message || 'Search failed');
            }
        } catch (error) {
            console.error('Search error:', error);
            this.setLoadingState(false);
            this.showError(error.message || 'Failed to start search. Please try again.');
        }
    }

    setLoadingState(loading) {
        const searchButton = document.querySelector('.search-button');
        const buttonText = searchButton.querySelector('.button-text');
        const loadingSpinner = searchButton.querySelector('.loading-spinner');

        if (loading) {
            searchButton.classList.add('loading');
            searchButton.disabled = true;
        } else {
            searchButton.classList.remove('loading');
            searchButton.disabled = false;
        }
    }

    hideAllSections() {
        const sections = ['progressSection', 'resultsSection', 'errorSection'];
        sections.forEach(id => {
            const section = document.getElementById(id);
            if (section) {
                section.classList.add('hidden');
            }
        });
    }

    showProgressSection() {
        this.hideAllSections();
        const progressSection = document.getElementById('progressSection');
        if (progressSection) {
            progressSection.classList.remove('hidden');
            progressSection.classList.add('slide-up');
            
            // Update progress header
            const progressHeader = progressSection.querySelector('.progress-header h3');
            if (progressHeader) {
                progressHeader.textContent = 'Searching both sessions...';
            }
            
            // Smooth scroll to progress section
            setTimeout(() => {
                progressSection.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
            }, 100);
        }
    }

    startDirectResultPolling() {
        if (!this.currentSessionId) return;

        // Clear any existing interval
        if (this.resultInterval) {
            clearInterval(this.resultInterval);
        }

        // Start polling immediately, then every 1 second for results
        this.pollForResults();
        
        this.resultInterval = setInterval(() => {
            this.pollForResults();
        }, 1000); // Poll every 1 second
    }
    
    async pollForResults() {
        if (!this.currentSessionId) return;
        
        try {
            const response = await fetch(`/api/progress/${this.currentSessionId}`);
            
            if (!response.ok) {
                if (response.status === 404) {
                    // Session not found yet, wait a bit more
                    console.log('Session not found yet, retrying...');
                    return;
                }
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();

            if (data.status === 'completed') {
                this.stopResultPolling();
                this.setLoadingState(false);
                
                // Check if we have results
                if (data.results && Array.isArray(data.results) && data.results.length > 0) {
                    console.log('✅ Search completed successfully with results:', data.results.length);
                    this.showResults(data.results);
                } else {
                    console.log('ℹ️ Search completed but no results found');
                    const errorMessage = data.message || 'No exam seats found for the provided details. Please verify your roll number and date.';
                    this.showError(errorMessage);
                }
            } else if (data.status === 'error') {
                this.stopResultPolling();
                this.setLoadingState(false);
                this.showError(data.message || 'Search failed. Please try again.');
            }
            // Keep polling if still searching
        } catch (error) {
            console.error('❌ Result polling error:', error);
            
            // Only stop polling and show error if we get multiple consecutive errors
            if (!this.errorCount) this.errorCount = 0;
            this.errorCount++;
            
            if (this.errorCount >= 5) {
                this.stopResultPolling();
                this.setLoadingState(false);
                this.showError('Connection lost. Please refresh the page and try again.');
            } else {
                console.log(`🔄 Retrying... (${this.errorCount}/5)`);
            }
        }
    }

    stopResultPolling() {
        if (this.resultInterval) {
            clearInterval(this.resultInterval);
            this.resultInterval = null;
        }
        this.errorCount = 0; // Reset error counter
        this.setLoadingState(false);
    }

    updateProgress(data) {
        const progressFill = document.getElementById('progressFill');
        const progressPercent = document.getElementById('progressPercent');
        const progressMessage = document.getElementById('progressMessage');

        if (progressFill) {
            const currentProgress = parseInt(progressFill.style.width) || 0;
            const targetProgress = Math.max(0, Math.min(100, data.progress || 0));
            
            // Smooth animation to target progress
            if (targetProgress > currentProgress) {
                // Animate progress more smoothly
                const increment = Math.max(1, Math.ceil((targetProgress - currentProgress) / 10));
                let animatedProgress = currentProgress;
                
                const animateStep = () => {
                    animatedProgress = Math.min(targetProgress, animatedProgress + increment);
                    progressFill.style.width = `${animatedProgress}%`;
                    
                    if (animatedProgress < targetProgress) {
                        setTimeout(animateStep, 50); // Smooth 50ms increments
                    }
                };
                
                animateStep();
            } else {
                progressFill.style.width = `${targetProgress}%`;
            }
            
            // Add smooth transition effect
            progressFill.style.transition = 'width 0.3s ease-out';
        }

        if (progressPercent) {
            // Animate percentage counter
            const currentPercent = parseInt(progressPercent.textContent) || 0;
            const targetPercent = data.progress || 0;
            
            if (targetPercent > currentPercent) {
                let animatedPercent = currentPercent;
                const increment = Math.max(1, Math.ceil((targetPercent - currentPercent) / 8));
                
                const animatePercent = () => {
                    animatedPercent = Math.min(targetPercent, animatedPercent + increment);
                    progressPercent.textContent = `${animatedPercent}%`;
                    
                    if (animatedPercent < targetPercent) {
                        setTimeout(animatePercent, 60);
                    }
                };
                
                animatePercent();
            } else {
                progressPercent.textContent = `${targetPercent}%`;
            }
        }

        if (progressMessage) {
            let message = data.message || 'Processing...';
            
            // Add more realistic time estimates based on actual progress
            if (data.progress >= 10 && data.progress < 40 && !message.includes('may take')) {
                message += ' (This may take 20-40 seconds)';
            } else if (data.progress >= 40 && data.progress < 70 && !message.includes('Almost done')) {
                message += ' (Almost done...)';
            } else if (data.progress >= 70 && data.progress < 95 && !message.includes('Finishing up')) {
                message += ' (Finishing up...)';
            }
            
            // Smooth message transition
            if (progressMessage.textContent !== message) {
                progressMessage.style.opacity = '0.7';
                setTimeout(() => {
                    progressMessage.textContent = message;
                    progressMessage.style.opacity = '1';
                }, 150);
            }
        }
        
        // Update section header based on progress (more responsive to actual progress)
        const progressHeader = document.querySelector('.progress-header h3');
        if (progressHeader && data.status === 'searching') {
            let headerText = 'Searching Exam Records...';
            
            if (data.progress >= 10 && data.progress < 35) {
                headerText = 'Connecting to Exam Portal...';
            } else if (data.progress >= 35 && data.progress < 60) {
                headerText = 'Loading Student Data...';
            } else if (data.progress >= 60 && data.progress < 85) {
                headerText = 'Processing Exam Records...';
            } else if (data.progress >= 85 && data.progress < 95) {
                headerText = 'Finalizing Results...';
            } else if (data.progress >= 95) {
                headerText = 'Almost Complete...';
            }
            
            if (progressHeader.textContent !== headerText) {
                progressHeader.style.opacity = '0.8';
                setTimeout(() => {
                    progressHeader.textContent = headerText;
                    progressHeader.style.opacity = '1';
                }, 100);
            }
        }
    }

    showResults(results) {
        this.hideAllSections();
        
        if (!results || results.length === 0) {
            this.showError('No exam seat found for the provided details. Please check your roll number and exam date.');
            return;
        }

        const resultsSection = document.getElementById('resultsSection');
        const resultsContainer = document.getElementById('resultsContainer');

        if (resultsSection && resultsContainer) {
            // Clear previous results
            resultsContainer.innerHTML = '';

            // Create result cards
            results.forEach((result, index) => {
                const resultCard = this.createResultCard(result, index);
                resultsContainer.appendChild(resultCard);
            });

            // Add enhanced export section
            this.addEnhancedExportSection(resultsContainer);

            // Show results section
            resultsSection.classList.remove('hidden');
            resultsSection.classList.add('slide-up');

            // Smooth scroll to results
            setTimeout(() => {
                resultsSection.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start' 
                });
            }, 100);

            // Show success message
            const sessionText = results.length === 1 ? 'exam seat' : 'exam seats';
            this.showToast(`🎉 Found ${results.length} ${sessionText}!`, 'success');
            
            // Load export options with session extension
            this.loadExportOptionsWithExtension();
        }
    }

    addEnhancedExportSection(container) {
        const exportSection = document.createElement('div');
        exportSection.className = 'enhanced-export-section';
        exportSection.innerHTML = `
            <div class="export-header">
                <h3>📤 Export & Share Options</h3>
                <p>Choose how you'd like to save or share your exam details</p>
            </div>
            <div class="export-loading" id="exportLoading">
                <div class="loading-spinner"></div>
                <p>Loading export options...</p>
            </div>
            
            <div class="export-options" id="exportOptions" style="display: none;">
                <!-- Export options will be loaded here -->
            </div>
            
            <div class="export-preview" id="exportPreview" style="display: none;">
                <!-- Preview will be loaded here -->
            </div>
        `;

        container.appendChild(exportSection);
    }
    
    async loadExportOptionsWithExtension() {
        if (!this.currentSessionId) {
            console.warn('⚠️ No session ID available for export options');
            this.showExportError('No session available. Please search again.');
            return;
        }
        
        try {
            // First, extend the session to prevent expiration
            await this.extendSession();
            
            // Then load export options
            await this.loadExportOptions();
            
        } catch (error) {
            console.error('❌ Error in export options workflow:', error);
            this.showExportError('Failed to prepare export options. Please try again.');
        }
    }
    
    async extendSession() {
        if (!this.currentSessionId) return;
        
        try {
            const response = await fetch(`/api/sessions/extend/${this.currentSessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                console.log('✅ Session extended successfully');
            } else {
                console.warn('⚠️ Failed to extend session, but continuing...');
            }
        } catch (error) {
            console.warn('⚠️ Session extension failed:', error);
            // Continue anyway - export might still work
        }
    }

    async loadExportOptions() {
        if (!this.currentSessionId) {
            console.warn('⚠️ No session ID available for export options');
            this.showExportError('No session available. Please search again.');
            return;
        }
        
        try {
            console.log('📤 Loading export options for session:', this.currentSessionId);
            
            const response = await fetch(`/api/export/${this.currentSessionId}/options`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache'
                }
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP ${response.status}: Failed to load export options`);
            }
            
            const data = await response.json();
            this.displayExportOptions(data);
            
        } catch (error) {
            console.error('❌ Error loading export options:', error);
            this.showExportError(error.message);
        }
    }
    
    showExportError(message) {
        const exportLoading = document.getElementById('exportLoading');
        if (exportLoading) {
            exportLoading.innerHTML = `
                <div class="export-error-container">
                    <div class="error-icon-wrapper">
                        <div class="error-icon">
                            <i class="fas fa-exclamation-triangle"></i>
                        </div>
                    </div>
                    <div class="error-content">
                        <h3 class="error-title">Unable to Load Export Options</h3>
                        <p class="error-message">Session not found. Please search again to generate fresh results.</p>
                        <div class="error-suggestion">
                            <p><i class="fas fa-lightbulb"></i> What to do:</p>
                            <ul>
                                <li>Click the Retry button below to refresh the export options.</li>
                            </ul>
                        </div>
                    </div>
                    <div class="error-actions">
                        <button onclick="seatFinder.loadExportOptionsWithExtension()" class="error-action-btn">
                            <i class="fas fa-redo"></i>
                            Retry
                        </button>
                    </div>
                </div>
            `;
        }
    }

    displayExportOptions(data) {
        console.log('📤 Displaying export options:', data);
        
        // Hide loading
        document.getElementById('exportLoading').style.display = 'none';
        
        // Show export options
        const exportOptions = document.getElementById('exportOptions');
        const exportPreview = document.getElementById('exportPreview');
        
        if (!exportOptions || !exportPreview) {
            console.error('❌ Export elements not found');
            return;
        }
        
        // Populate export options
        exportOptions.innerHTML = data.available_formats.map(format => {
            const escapedUrl = format.url.replace(/'/g, "\\'");
            return `
                <div class="export-option" data-type="${format.type}">
                    <div class="export-icon">${format.icon}</div>
                    <div class="export-info">
                        <h4>${format.name}</h4>
                        <p>${format.description}</p>
                    </div>
                    <button class="export-btn" onclick="handleExportClick('${format.type}', '${escapedUrl}', ${format.external || false})">
                        ${format.external ? 'Open' : 'Download'}
                        <i class="fas fa-${format.external ? 'external-link-alt' : 'download'}"></i>
                    </button>
                </div>
            `;
        }).join('');
        
        // Show sections
        exportOptions.style.display = 'block';
        
        console.log('✅ Export options displayed successfully');
    }

    async handleExport(type, url, isExternal) {
        console.log(`🚀 Handling export: ${type}, URL: ${url}, External: ${isExternal}`);
        
        if (isExternal) {
            // Open external link (WhatsApp, Calendar)
            window.open(url, '_blank');
            this.showToast(`Opening ${type} sharing...`, 'info');
        } else {
            // Handle download
            try {
                this.showToast('Preparing download...', 'info');
                
                // Add retry logic for failed downloads
                let retries = 3;
                let response;
                
                while (retries > 0) {
                    response = await fetch(url, {
                        method: 'GET',
                        headers: {
                            'Cache-Control': 'no-cache'
                        }
                    });
                    
                    if (response.ok) {
                        break;
                    } else if (response.status === 404 || response.status === 400) {
                        // Session expired or invalid - don't retry
                        const errorData = await response.json();
                        throw new Error(errorData.error || 'Session expired. Please search again.');
                    } else {
                        retries--;
                        if (retries > 0) {
                            console.log(`⚠️ Download failed, retrying... (${retries} attempts left)`);
                            await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second
                        }
                    }
                }
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Export failed after retries');
                }

                // Create download link
                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                
                // Set filename based on type
                const timestamp = new Date().getTime();
                const extensions = {
                    'pdf': 'pdf',
                    'csv': 'csv'
                };
                
                a.download = `exam_${type}_${timestamp}.${extensions[type] || 'file'}`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(downloadUrl);

                this.showToast(`${type.toUpperCase()} downloaded successfully!`, 'success');
            } catch (error) {
                console.error('❌ Export error:', error);
                this.showToast(`Export failed: ${error.message}`, 'error');
                
                // If session expired, suggest searching again
                if (error.message.includes('Session expired') || error.message.includes('404')) {
                    setTimeout(() => {
                        this.showToast('Please search again to export results', 'warning');
                    }, 2000);
                }
            }
        }
    }



    async exportResults() {
        // Legacy export function - redirect to enhanced options
        if (!this.currentSessionId) {
            this.showToast('No results to export', 'error');
            return;
        }

        // Scroll to export section
        const exportSection = document.querySelector('.enhanced-export-section');
        if (exportSection) {
            exportSection.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
            this.showToast('Choose an export option below', 'info');
        } else {
            this.showToast('Export options not available', 'error');
        }
    }

    createResultCard(result, index) {
        const card = document.createElement('div');
        card.className = 'result-card';
        card.style.animationDelay = `${index * 0.1}s`;

        // Determine session badge color
        const sessionColor = result.session === 'FN' ? '#007AFF' : '#5856D6';

        card.innerHTML = `
            <div class="result-header">
                <div class="exam-info">
                    <div class="exam-icon">
                        <i class="fas fa-chair"></i>
                    </div>
                    <div class="exam-details">
                        <h4>Exam ${index + 1}</h4>
                        <p>${result.date}</p>
                    </div>
                </div>
                <div class="session-badge" style="background-color: ${sessionColor}">
                    ${result.session_name}
                </div>
            </div>
            <div class="result-grid">
                <div class="result-field">
                    <div class="field-label">Room Number</div>
                    <div class="field-value room">${result.room_number}</div>
                </div>
                <div class="result-field">
                    <div class="field-label">Seat Number</div>
                    <div class="field-value seat">${result.seat_number}</div>
                </div>
                <div class="result-field">
                    <div class="field-label">Venue</div>
                    <div class="field-value venue">${result.venue_name || 'Main Campus'}</div>
                </div>
                <div class="result-field">
                    <div class="field-label">Department</div>
                    <div class="field-value">${result.department}</div>
                </div>
                <div class="result-field">
                    <div class="field-label">Registration</div>
                    <div class="field-value">${result.registration_number}</div>
                </div>
            </div>
        `;

        return card;
    }

    showError(message) {
        this.hideAllSections();
        
        const errorSection = document.getElementById('errorSection');
        const errorMessage = document.getElementById('errorMessage');

        if (errorSection && errorMessage) {
            errorMessage.textContent = message;
            errorSection.classList.remove('hidden');
            errorSection.classList.add('slide-up');

            // Smooth scroll to error section
            setTimeout(() => {
                errorSection.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
            }, 100);
        }

        this.showToast(message, 'error');
    }

    async resetSearch() {
        // Clear ALL sessions on the server when user clicks "Search Again"
        try {
            const response = await fetch('/api/clear-sessions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();
            if (data.success) {
                console.log('✅ All sessions cleared successfully');
                this.showToast('All sessions cleared - ready for new search', 'success');
            } else {
                console.warn('⚠️ Session clear failed:', data.message);
            }
        } catch (error) {
            console.error('❌ Error clearing sessions:', error);
            // Continue with reset even if server clear fails
        }

        // Clear form
        const searchForm = document.getElementById('searchForm');
        if (searchForm) {
            searchForm.reset();
        }

        // Clear validation states
        document.querySelectorAll('.input-wrapper').forEach(wrapper => {
            wrapper.classList.remove('success', 'error');
        });

        // Hide all sections
        this.hideAllSections();

        // Stop any ongoing polling
        this.stopResultPolling();

        // Reset session - but keep a backup for debugging
        if (this.currentSessionId) {
            console.log('🔄 Resetting search, previous session:', this.currentSessionId);
        }
        this.currentSessionId = null;

        // Scroll to search section
        const searchSection = document.querySelector('.search-section');
        if (searchSection) {
            searchSection.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center' 
            });
        }
    }

    handleNavigation(e) {
        e.preventDefault();
        
        const targetId = e.target.getAttribute('href');
        const targetSection = document.querySelector(targetId);
        
        if (targetSection) {
            // Update active nav link
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove('active');
            });
            e.target.classList.add('active');

            // Smooth scroll to section
            targetSection.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
        }
    }

    handleKeyboard(e) {
        // Escape key to reset search
        if (e.key === 'Escape') {
            this.resetSearch();
        }

        // Enter key on results to export
        if (e.key === 'Enter' && !document.querySelector('#searchForm:focus-within')) {
            const resultsSection = document.getElementById('resultsSection');
            if (resultsSection && !resultsSection.classList.contains('hidden')) {
                this.exportResults();
            }
        }
    }

    handleResize() {
        // Adjust floating card animation for mobile
        const floatingCard = document.querySelector('.floating-card');
        if (floatingCard && window.innerWidth < 768) {
            floatingCard.style.transform = 'none';
        }
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        const toastIcon = toast.querySelector('.toast-icon');
        const toastMessage = toast.querySelector('.toast-message');

        // Set icon based on type
        let iconClass = 'fas fa-info-circle';
        if (type === 'success') iconClass = 'fas fa-check-circle';
        else if (type === 'error') iconClass = 'fas fa-exclamation-circle';
        else if (type === 'warning') iconClass = 'fas fa-exclamation-triangle';

        toastIcon.className = `toast-icon ${iconClass}`;
        toastMessage.textContent = message;
        toast.className = `toast ${type}`;

        // Show toast
        toast.classList.remove('hidden');

        // Auto hide after 5 seconds for longer messages
        setTimeout(() => {
            toast.classList.add('hidden');
        }, 5000);
    }
}

// Global helper functions
function scrollToSearch() {
    const searchSection = document.querySelector('.search-section');
    if (searchSection) {
        searchSection.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center' 
        });
    }
}

function scrollToAbout() {
    const aboutSection = document.querySelector('.about-section');
    if (aboutSection) {
        aboutSection.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }
}

// Global export helper functions
function handleExportClick(type, url, isExternal) {
    console.log(`🚀 Export clicked: ${type}, URL: ${url}, External: ${isExternal}`);
    
    if (!seatFinder) {
        console.error('❌ SeatFinder app not initialized');
        return;
    }
    
    seatFinder.handleExport(type, url, isExternal);
}



// Initialize app when DOM is loaded
let seatFinder; // Make it global

document.addEventListener('DOMContentLoaded', () => {
    seatFinder = new SeatFinderApp(); // Assign to global variable
    
    // Add some visual flair
    console.log(`
    ╔══════════════════════════════════════╗
    ║        SRM Exam Seat Finder          ║
    ║     🎓 Find Your Seat Instantly      ║
    ║      Searching FN & AN Sessions      ║
    ╚══════════════════════════════════════╝
    `);
});

// Add CSS classes for form validation styles
const style = document.createElement('style');
style.textContent = `
    .input-wrapper.success input {
        border-color: var(--success-color);
        box-shadow: 0 0 0 3px rgba(52, 199, 89, 0.1);
    }

    .input-wrapper.error input {
        border-color: var(--error-color);
        box-shadow: 0 0 0 3px rgba(255, 59, 48, 0.1);
    }

    .input-wrapper.success i {
        color: var(--success-color);
    }

    .input-wrapper.error i {
        color: var(--error-color);
    }

    .result-card {
        animation: slideInUp 0.6s ease-out forwards;
        opacity: 0;
        transform: translateY(30px);
    }

    @keyframes slideInUp {
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .floating-card {
        transition: transform 0.1s ease-out;
    }

    .progress-fill {
        transition: width 0.5s ease-out !important;
    }
    
    .error-actions {
        display: flex;
        gap: 10px;
        margin-top: 15px;
        justify-content: center;
        flex-wrap: wrap;
    }
    
    .retry-btn, .search-again-btn {
        padding: 8px 16px;
        border: none;
        border-radius: 6px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    .retry-btn {
        background: var(--primary-color);
        color: white;
    }
    
    .retry-btn:hover {
        background: var(--primary-hover);
        transform: translateY(-1px);
    }
    
    .search-again-btn {
        background: var(--secondary-color);
        color: var(--text-color);
        border: 1px solid var(--border-color);
    }
    
    .search-again-btn:hover {
        background: var(--hover-color);
        transform: translateY(-1px);
    }

    @media (prefers-reduced-motion: reduce) {
        .floating-card {
            animation: none;
            transform: none !important;
        }
        
        .result-card {
            animation: none;
            opacity: 1;
            transform: none;
        }
        
        .progress-fill {
            transition: none !important;
        }
    }
`;
document.head.appendChild(style);



function exportPDF() {
    // Legacy function - redirect to new export system
    if (seatFinder && seatFinder.currentSessionId) {
        window.location.href = `/api/export/${seatFinder.currentSessionId}/pdf`;
            } else {
        showError('No session available for export');
}
}

// Helper functions for export
function getSeatDetails() {
    // Extract seat details from the current results
    if (seatFinder && seatFinder.currentResults && seatFinder.currentResults.length > 0) {
        const result = seatFinder.currentResults[0]; // Take first result
        return {
            registration_number: result.registration_number,
            date: result.date,
            session: result.session,
            session_name: result.session_name,
            room_number: result.room_number,
            seat_number: result.seat_number,
            department: result.department
        };
    }
    return null;
}

function showLoading(message) {
    if (seatFinder) {
        seatFinder.showToast(message, 'info');
    }
}

function hideLoading() {
    // Loading is handled by toast auto-hide
}

function showSuccess(message) {
    if (seatFinder) {
        seatFinder.showToast(message, 'success');
    }
}

function showError(message) {
    if (seatFinder) {
        seatFinder.showToast(message, 'error');
    }
}

function updateExportStats(format) {
    // Track export statistics (optional)
    console.log(`📊 Export completed: ${format}`);
} 