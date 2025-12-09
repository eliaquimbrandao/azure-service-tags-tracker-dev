/**
 * Subscription Page JavaScript
 * Handles email subscription form with service and region filtering
 */

class SubscriptionManager {
    constructor() {
        this.services = [];
        this.selectedServices = new Set();
        this.selectedRegions = new Set();
        this.currentCategory = 'all';
        this.searchTerm = '';
        this.currentPage = 1;
        this.itemsPerPage = 50;
        this.allRegions = this.getAllAzureRegions();
        this.premiumLocked = true; // Filtered targeting is premium-only for now
        this.planStatus = { plan: 'free', status: 'inactive', expires_at: null };
        // API endpoint - update this when deploying to Vercel
        this.apiBaseUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'http://localhost:3000'  // Local development
            : 'https://azure-service-tags-tracker-dev.vercel.app';  // Production Vercel API
        this.init();
    }

    getAllAzureRegions() {
        // Complete list of Azure regions
        return [
            { id: 'eastus', name: 'East US' },
            { id: 'eastus2', name: 'East US 2' },
            { id: 'westus', name: 'West US' },
            { id: 'westus2', name: 'West US 2' },
            { id: 'westus3', name: 'West US 3' },
            { id: 'centralus', name: 'Central US' },
            { id: 'northcentralus', name: 'North Central US' },
            { id: 'southcentralus', name: 'South Central US' },
            { id: 'westcentralus', name: 'West Central US' },
            { id: 'canadacentral', name: 'Canada Central' },
            { id: 'canadaeast', name: 'Canada East' },
            { id: 'brazilsouth', name: 'Brazil South' },
            { id: 'brazilsoutheast', name: 'Brazil Southeast' },
            { id: 'mexicocentral', name: 'Mexico Central' },
            { id: 'chilecentral', name: 'Chile Central' },
            { id: 'northeurope', name: 'North Europe' },
            { id: 'westeurope', name: 'West Europe' },
            { id: 'uksouth', name: 'UK South' },
            { id: 'ukwest', name: 'UK West' },
            { id: 'francecentral', name: 'France Central' },
            { id: 'francesouth', name: 'France South' },
            { id: 'germanywestcentral', name: 'Germany West Central' },
            { id: 'germanynorth', name: 'Germany North' },
            { id: 'norwayeast', name: 'Norway East' },
            { id: 'norwaywest', name: 'Norway West' },
            { id: 'swedencentral', name: 'Sweden Central' },
            { id: 'swedensouth', name: 'Sweden South' },
            { id: 'switzerlandnorth', name: 'Switzerland North' },
            { id: 'switzerlandwest', name: 'Switzerland West' },
            { id: 'polandcentral', name: 'Poland Central' },
            { id: 'spaincentral', name: 'Spain Central' },
            { id: 'italynorth', name: 'Italy North' },
            { id: 'austriaeast', name: 'Austria East' },
            { id: 'belgiumcentral', name: 'Belgium Central' },
            { id: 'eastasia', name: 'East Asia' },
            { id: 'southeastasia', name: 'Southeast Asia' },
            { id: 'australiaeast', name: 'Australia East' },
            { id: 'australiasoutheast', name: 'Australia Southeast' },
            { id: 'australiacentral', name: 'Australia Central' },
            { id: 'australiacentral2', name: 'Australia Central 2' },
            { id: 'newzealandnorth', name: 'New Zealand North' },
            { id: 'japaneast', name: 'Japan East' },
            { id: 'japanwest', name: 'Japan West' },
            { id: 'koreacentral', name: 'Korea Central' },
            { id: 'koreasouth', name: 'Korea South' },
            { id: 'centralindia', name: 'Central India' },
            { id: 'southindia', name: 'South India' },
            { id: 'westindia', name: 'West India' },
            { id: 'indonesiacentral', name: 'Indonesia Central' },
            { id: 'malaysiawest', name: 'Malaysia West' },
            { id: 'uaenorth', name: 'UAE North' },
            { id: 'uaecentral', name: 'UAE Central' },
            { id: 'qatarcentral', name: 'Qatar Central' },
            { id: 'israelcentral', name: 'Israel Central' },
            { id: 'southafricanorth', name: 'South Africa North' },
            { id: 'southafricawest', name: 'South Africa West' }
        ];
    }

    async init() {
        await this.loadServices();
        this.setupEventListeners();
        this.renderServices();
    }

    async loadServices() {
        try {
            const response = await fetch('data/current.json');
            const data = await response.json();
            
            // Extract unique services from the Azure data
            this.services = data.values.map(service => ({
                id: service.id,
                name: service.name,
                properties: service.properties || {},
                category: this.categorizeService(service.name)
            }));

            this.updateCategoryCounts();
        } catch (error) {
            console.error('Error loading services:', error);
            this.showError('Failed to load services. Please try again later.');
        }
    }

    categorizeService(serviceName) {
        const name = serviceName.toLowerCase();
        
        // Popular services
        const popular = ['azurecloud', 'storage', 'sql', 'azureactivedirectory', 'azuremonitor'];
        if (popular.some(p => name.includes(p))) return 'popular';
        
        // Compute
        if (name.includes('virtualmachine') || name.includes('compute') || name.includes('batch') || name.includes('container')) {
            return 'compute';
        }
        
        // Storage
        if (name.includes('storage') || name.includes('backup') || name.includes('databox')) {
            return 'storage';
        }
        
        // Database
        if (name.includes('sql') || name.includes('cosmos') || name.includes('database') || name.includes('redis')) {
            return 'database';
        }
        
        // Networking
        if (name.includes('network') || name.includes('frontdoor') || name.includes('firewall') || name.includes('vpn') || name.includes('gateway')) {
            return 'networking';
        }
        
        return 'all';
    }

    updateCategoryCounts() {
        const counts = {
            all: this.services.length,
            popular: this.services.filter(s => s.category === 'popular').length,
            compute: this.services.filter(s => s.category === 'compute').length,
            storage: this.services.filter(s => s.category === 'storage').length,
            database: this.services.filter(s => s.category === 'database').length,
            networking: this.services.filter(s => s.category === 'networking').length
        };

        Object.entries(counts).forEach(([category, count]) => {
            const countElement = document.getElementById(`${category}Count`);
            if (countElement) {
                countElement.textContent = count;
            }
        });
    }

    setupEventListeners() {
        // Subscription type radio buttons
        const radioButtons = document.querySelectorAll('input[name="subscriptionType"]');
        const filteredRadio = document.querySelector('input[name="subscriptionType"][value="filtered"]');
        radioButtons.forEach(radio => {
            radio.addEventListener('change', (e) => {
                const filterSection = document.getElementById('filterSection');
                if (e.target.value === 'filtered') {
                    // Premium gating: keep hidden even if user tries to toggle via devtools
                    filterSection.style.display = 'none';
                    this.showError('Filtered alerts by service/region/IP are a premium feature coming soon.');
                    // Revert to all changes
                    const allRadio = document.querySelector('input[name="subscriptionType"][value="all"]');
                    if (allRadio) allRadio.checked = true;
                } else {
                    filterSection.style.display = 'none';
                }
            });
        });

        // Ensure filtered option stays disabled (defense in depth)
        if (filteredRadio) {
            filteredRadio.disabled = true;
        }

        // Premium lock: disable service and region controls
        if (this.premiumLocked) {
            const serviceFilter = document.getElementById('serviceFilter');
            const regionFilter = document.getElementById('regionFilter');
            const selectAllBtn = document.getElementById('selectAllBtn');
            const clearAllBtn = document.getElementById('clearAllBtn');
            if (serviceFilter) {
                serviceFilter.disabled = true;
                serviceFilter.placeholder = 'Premium feature: service/IP targeting coming soon';
            }
            if (regionFilter) {
                regionFilter.disabled = true;
                regionFilter.placeholder = 'Premium feature: region/IP targeting coming soon';
            }
            if (selectAllBtn) selectAllBtn.disabled = true;
            if (clearAllBtn) clearAllBtn.disabled = true;
        }

        // Plan status check on email blur/change
        const emailInput = document.getElementById('email');
        const upgradeBtn = document.getElementById('upgradeBtn');
        if (emailInput) {
            emailInput.addEventListener('blur', () => this.checkPlanStatus());
            emailInput.addEventListener('change', () => this.checkPlanStatus());
        }
        if (upgradeBtn) {
            upgradeBtn.addEventListener('click', () => this.startUpgrade());
        }

        // Service filter search
        const serviceFilter = document.getElementById('serviceFilter');
        if (serviceFilter) {
            serviceFilter.addEventListener('input', (e) => {
                this.searchTerm = e.target.value.toLowerCase();
                this.currentPage = 1;
                this.renderServices();
            });
        }

        // Category buttons
        const categoryButtons = document.querySelectorAll('.category-btn');
        categoryButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const clickedCategory = button.dataset.category;
                const wasActive = button.classList.contains('active');
                
                // Remove active from all buttons
                categoryButtons.forEach(btn => btn.classList.remove('active'));
                
                // Toggle logic
                if (wasActive && clickedCategory === this.currentCategory) {
                    // Clicking the same active button deselects it
                    this.currentCategory = null;
                    // Don't add active class to any button
                } else {
                    // Select the clicked button
                    button.classList.add('active');
                    this.currentCategory = clickedCategory;
                }
                
                this.currentPage = 1;
                this.renderServices();
            });
        });

        // Region chips
        const regionChips = document.querySelectorAll('.chip[data-region]');
        regionChips.forEach(chip => {
            chip.addEventListener('click', (e) => {
                const region = chip.dataset.region;
                
                if (region === 'all') {
                    // Toggle "All Regions"
                    if (this.selectedRegions.has('all') || this.selectedRegions.size === 0) {
                        // If "all" is selected or nothing selected, clear everything
                        this.selectedRegions.clear();
                        regionChips.forEach(c => c.classList.remove('active'));
                    } else {
                        // Select "all", deselect others
                        this.selectedRegions.clear();
                        this.selectedRegions.add('all');
                        regionChips.forEach(c => c.classList.remove('active'));
                        chip.classList.add('active');
                    }
                } else {
                    // Remove "all" if it was selected
                    this.selectedRegions.delete('all');
                    const allChip = document.querySelector('.chip[data-region="all"]');
                    if (allChip) allChip.classList.remove('active');
                    
                    // Toggle this specific region
                    if (this.selectedRegions.has(region)) {
                        this.selectedRegions.delete(region);
                        chip.classList.remove('active');
                    } else {
                        this.selectedRegions.add(region);
                        chip.classList.add('active');
                    }
                }
            });
        });

        // Region search functionality
        const regionFilter = document.getElementById('regionFilter');
        const regionDropdown = document.getElementById('regionDropdown');
        
        if (regionFilter && regionDropdown) {
            // Show dropdown on focus
            regionFilter.addEventListener('focus', () => {
                this.updateRegionDropdown(regionFilter.value);
            });

            // Search as user types
            regionFilter.addEventListener('input', (e) => {
                this.updateRegionDropdown(e.target.value);
            });

            // Hide dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!regionFilter.contains(e.target) && !regionDropdown.contains(e.target)) {
                    regionDropdown.style.display = 'none';
                }
            });
        }

        // Select All / Clear All buttons
        const selectAllBtn = document.getElementById('selectAllBtn');
        const clearAllBtn = document.getElementById('clearAllBtn');
        
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => {
                this.selectAllOnPage();
            });
        }
        
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => {
                this.clearAllSelections();
            });
        }

        // Form submission
        const form = document.getElementById('subscriptionForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleSubmit();
            });
        }
    }

    renderServices() {
        const serviceList = document.getElementById('serviceList');
        if (!serviceList) return;

        // Premium lock: show banner and bail
        if (this.premiumLocked) {
            serviceList.innerHTML = '<div class="premium-locked-msg">Targeted service selection is a premium feature coming soon.</div>';
            return;
        }

        // Filter services by category
        let filteredServices = this.services;
        if (this.currentCategory && this.currentCategory !== 'all') {
            filteredServices = this.services.filter(s => s.category === this.currentCategory);
        }

        // Apply search filter
        if (this.searchTerm) {
            if (this.isIpQuery(this.searchTerm)) {
                filteredServices = filteredServices.filter(service => this.serviceMatchesIp(service, this.searchTerm));
            } else {
                filteredServices = filteredServices.filter(service => 
                    service.name.toLowerCase().includes(this.searchTerm) ||
                    service.id.toLowerCase().includes(this.searchTerm)
                );
            }
        }

        if (filteredServices.length === 0) {
            serviceList.innerHTML = '<div class="loading-services">No services found</div>';
            return;
        }

        // Pagination
        const totalPages = Math.ceil(filteredServices.length / this.itemsPerPage);
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const paginatedServices = filteredServices.slice(startIndex, endIndex);

        // Render service items (only current page)
        const servicesHtml = paginatedServices.map(service => `
            <div class="service-item" data-service-id="${service.id}">
                <input type="checkbox" 
                    id="service-${service.id}" 
                    value="${service.id}"
                    ${this.selectedServices.has(service.id) ? 'checked' : ''}>
                <label for="service-${service.id}" class="service-item-content">
                    <div class="service-name">${this.escapeHtml(service.name)}</div>
                    <div class="service-meta">ID: ${this.escapeHtml(service.id)}</div>
                </label>
            </div>
        `).join('');

        // Pagination controls
        const paginationHtml = filteredServices.length > this.itemsPerPage ? `
            <div class="pagination-controls">
                <button class="pagination-btn" id="prevPage" ${this.currentPage === 1 ? 'disabled' : ''}>
                    ← Previous
                </button>
                <span class="pagination-info">
                    Page ${this.currentPage} of ${totalPages} 
                    <span class="pagination-count">(${filteredServices.length} services)</span>
                </span>
                <button class="pagination-btn" id="nextPage" ${this.currentPage === totalPages ? 'disabled' : ''}>
                    Next →
                </button>
            </div>
        ` : `
            <div class="pagination-controls">
                <span class="pagination-info">
                    ${filteredServices.length} service${filteredServices.length !== 1 ? 's' : ''}
                </span>
            </div>
        `;

        serviceList.innerHTML = servicesHtml + paginationHtml;

        // Add checkbox event listeners
        serviceList.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const serviceId = e.target.value;
                if (e.target.checked) {
                    this.selectedServices.add(serviceId);
                } else {
                    this.selectedServices.delete(serviceId);
                }
                this.updateSelectedCount();
            });
        });

        // Add pagination event listeners
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                if (this.currentPage > 1) {
                    this.currentPage--;
                    this.renderServices();
                    serviceList.scrollTop = 0;
                }
            });
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                if (this.currentPage < totalPages) {
                    this.currentPage++;
                    this.renderServices();
                    serviceList.scrollTop = 0;
                }
            });
        }

        this.updateSelectedCount();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    filterServices(searchTerm) {
        // This method is now handled in renderServices
        this.searchTerm = searchTerm.toLowerCase();
        this.currentPage = 1;
        this.renderServices();
    }

    updateSelectedCount() {
        const countElement = document.querySelector('.selected-count');
        if (countElement) {
            countElement.textContent = `${this.selectedServices.size} service${this.selectedServices.size !== 1 ? 's' : ''}`;
        }
    }

    selectAllOnPage() {
        // Select all visible services on current page
        const checkboxes = document.querySelectorAll('.service-item input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            if (!checkbox.checked) {
                checkbox.checked = true;
                this.selectedServices.add(checkbox.value);
            }
        });
        this.updateSelectedCount();
    }

    clearAllSelections() {
        // Clear all selected services
        this.selectedServices.clear();
        // Uncheck all visible checkboxes
        const checkboxes = document.querySelectorAll('.service-item input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        this.updateSelectedCount();
    }

    updateRegionDropdown(searchTerm) {
        const dropdown = document.getElementById('regionDropdown');
        if (!dropdown) return;

        if (this.premiumLocked) {
            dropdown.innerHTML = '<div class="region-dropdown-item no-results">Region/IP targeting is premium-only (coming soon)</div>';
            dropdown.style.display = 'block';
            return;
        }

        const term = searchTerm.toLowerCase().trim();

        // Filter regions: support IP lookups by matching services that contain the IP
        let filteredRegions = this.allRegions;
        if (term) {
            if (this.isIpQuery(term)) {
                const ipRegions = this.getRegionsForIp(term);
                filteredRegions = this.allRegions.filter(region => ipRegions.has(region.id));
            } else {
                filteredRegions = this.allRegions.filter(region => 
                    region.name.toLowerCase().includes(term) ||
                    region.id.toLowerCase().includes(term)
                );
            }
        }

        // Remove already selected regions from dropdown
        filteredRegions = filteredRegions.filter(region => !this.selectedRegions.has(region.id));

        if (filteredRegions.length === 0) {
            dropdown.innerHTML = '<div class="region-dropdown-item no-results">No regions found</div>';
            dropdown.style.display = 'block';
            return;
        }

        // Limit to 10 results
        const limitedRegions = filteredRegions.slice(0, 10);
        
        dropdown.innerHTML = limitedRegions.map(region => `
            <div class="region-dropdown-item" data-region-id="${this.escapeHtml(region.id)}">
                <span class="region-name">${this.highlightMatch(this.escapeHtml(region.name), term)}</span>
                <span class="region-id">${this.escapeHtml(region.id)}</span>
            </div>
        `).join('');

        dropdown.style.display = 'block';

        // Add click handlers to dropdown items
        const items = dropdown.querySelectorAll('.region-dropdown-item:not(.no-results)');
        items.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const regionId = item.getAttribute('data-region-id');
                if (regionId) {
                    this.addRegion(regionId);
                    const regionFilter = document.getElementById('regionFilter');
                    if (regionFilter) {
                        regionFilter.value = '';
                    }
                    dropdown.style.display = 'none';
                }
            });
        });
    }

    highlightMatch(text, searchTerm) {
        if (!searchTerm) return text;
        const regex = new RegExp(`(${this.escapeRegex(searchTerm)})`, 'gi');
        return text.replace(regex, '<strong>$1</strong>');
    }

    escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    isIpQuery(term) {
        const t = term.trim();
        return this.isIPv4(t) || this.isIPv4Cidr(t);
    }

    isIPv4(ip) {
        const match = ip.match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);
        if (!match) return false;
        return match.slice(1).every(octet => Number(octet) >= 0 && Number(octet) <= 255);
    }

    isIPv4Cidr(cidr) {
        const parts = cidr.split('/');
        if (parts.length !== 2) return false;
        const [ip, prefix] = parts;
        const prefixNum = Number(prefix);
        return this.isIPv4(ip) && Number.isInteger(prefixNum) && prefixNum >= 0 && prefixNum <= 32;
    }

    ipToInt(ip) {
        return ip.split('.').reduce((acc, oct) => (acc << 8) + Number(oct), 0) >>> 0;
    }

    ipInCidr(ip, cidr) {
        if (!this.isIPv4(ip)) return false;
        if (!this.isIPv4Cidr(cidr)) return false;
        const [network, prefix] = cidr.split('/');
        const maskBits = Number(prefix);
        const ipInt = this.ipToInt(ip);
        const networkInt = this.ipToInt(network);
        const mask = maskBits === 0 ? 0 : (~0 << (32 - maskBits)) >>> 0;
        return (ipInt & mask) === (networkInt & mask);
    }

    serviceMatchesIp(service, searchTerm) {
        const prefixes = (service.properties && service.properties.addressPrefixes) || [];
        const term = searchTerm.trim();
        if (!prefixes.length) return false;

        // Exact CIDR match
        if (this.isIPv4Cidr(term)) {
            return prefixes.some(p => p === term);
        }

        // IP match inside any CIDR
        if (this.isIPv4(term)) {
            return prefixes.some(p => {
                if (this.isIPv4Cidr(p)) return this.ipInCidr(term, p);
                if (this.isIPv4(p)) return p === term;
                return false;
            });
        }

        return false;
    }

    getRegionsForIp(searchTerm) {
        const regions = new Set();
        const term = searchTerm.trim();
        if (!term) return regions;

        this.services.forEach(service => {
            const regionId = (service.properties && service.properties.region) || '';
            if (!regionId) return;
            if (this.serviceMatchesIp(service, term)) {
                regions.add(regionId.toLowerCase());
            }
        });
        return regions;
    }

    addRegion(regionId) {
        this.selectedRegions.add(regionId);
        this.renderSelectedRegionTags();
        this.updateRegionDropdown(''); // Refresh dropdown
    }

    removeRegion(regionId) {
        this.selectedRegions.delete(regionId);
        this.renderSelectedRegionTags();
        this.updateRegionDropdown(document.getElementById('regionFilter').value); // Refresh dropdown
    }

    renderSelectedRegionTags() {
        const tagsContainer = document.getElementById('selectedRegionsTags');
        if (!tagsContainer) return;

        if (this.selectedRegions.size === 0) {
            tagsContainer.style.display = 'none';
            return;
        }

        tagsContainer.style.display = 'flex';
        
        const tags = Array.from(this.selectedRegions).map(regionId => {
            const region = this.allRegions.find(r => r.id === regionId);
            if (!region) return '';
            
            return `
                <div class="region-tag" data-region-id="${regionId}">
                    <span class="region-tag-name">${region.name}</span>
                    <button type="button" class="region-tag-remove" data-region-id="${regionId}">×</button>
                </div>
            `;
        }).join('');

        tagsContainer.innerHTML = tags;

        // Add remove handlers
        tagsContainer.querySelectorAll('.region-tag-remove').forEach(btn => {
            btn.addEventListener('click', () => {
                this.removeRegion(btn.dataset.regionId);
            });
        });
    }

    async handleSubmit() {
        const email = document.getElementById('email').value;
        const subscriptionType = document.querySelector('input[name="subscriptionType"]:checked').value;
        
        const subscriptionData = {
            email: email,
            subscriptionType: subscriptionType,
            selectedServices: subscriptionType === 'filtered' ? Array.from(this.selectedServices) : [],
            selectedRegions: subscriptionType === 'filtered' ? Array.from(this.selectedRegions) : []
        };

        // Validation
        if (subscriptionType === 'filtered') {
            this.showError('Filtered alerts are a premium feature. Please select "All Changes" to subscribe.');
            return;
        }

        // Disable submit button
        const submitBtn = document.getElementById('subscribeBtn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Submitting...</span>';

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/subscribe`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(subscriptionData)
            });

            let result = {};
            try {
                result = await response.json();
            } catch (parseError) {
                console.error('Failed to parse subscription response', parseError);
            }

            if (response.ok && result.success) {
                this.showSuccess('🎉 Subscription successful! Check your email for a confirmation message with your subscription details and unsubscribe link.');
                
                // Reset form after 3 seconds
                setTimeout(() => {
                    document.getElementById('subscriptionForm').reset();
                    this.selectedServices.clear();
                    this.selectedRegions.clear();
                    this.updateSelectedCount();
                    document.getElementById('filterSection').style.display = 'none';
                }, 3000);
            } else {
                // Handle API errors
                if (result.code === 'DUPLICATE_EMAIL') {
                    this.showError('⚠️ This email is already subscribed! Check your inbox for the confirmation email with your subscription details.');
                } else {
                    this.showError(result.error || 'Failed to create subscription. Please try again.');
                }
            }
            
        } catch (error) {
            console.error('Subscription error:', error);
            this.showError('Failed to connect to the server. Please check your internet connection and try again.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span class="btn-icon">📧</span><span class="btn-text">Subscribe for Free</span>';
        }
    }

    async checkPlanStatus() {
        const emailInput = document.getElementById('email');
        if (!emailInput || !emailInput.value) return;
        const email = emailInput.value.trim();
        if (!email) return;
        try {
            const res = await fetch(`${this.apiBaseUrl}/api/plan_status?email=${encodeURIComponent(email)}`);
            const data = await res.json();
            if (res.ok && data.success) {
                this.planStatus = data.plan || { plan: 'free', status: 'inactive' };
                this.applyPlanStatus();
            }
        } catch (err) {
            console.error('Plan status check failed', err);
        }
    }

    applyPlanStatus() {
        const statusText = document.getElementById('planStatusText');
        const statusWrap = document.getElementById('planStatus');
        const upgradeBtn = document.getElementById('upgradeBtn');
        const filteredRadio = document.querySelector('input[name="subscriptionType"][value="filtered"]');
        const serviceFilter = document.getElementById('serviceFilter');
        const regionFilter = document.getElementById('regionFilter');
        const selectAllBtn = document.getElementById('selectAllBtn');
        const clearAllBtn = document.getElementById('clearAllBtn');

        const isPremium = this.planStatus.plan === 'premium' && this.planStatus.status === 'active';
        if (statusWrap && statusText) {
            statusWrap.style.display = 'flex';
            if (isPremium) {
                statusText.textContent = 'Premium active — targeted filters unlocked.';
            } else {
                statusText.textContent = 'Free plan — upgrade to unlock targeted filters ($1/mo launch price).';
            }
        }

        this.premiumLocked = !isPremium;
        if (filteredRadio) {
            filteredRadio.disabled = this.premiumLocked;
            if (!this.premiumLocked) {
                filteredRadio.parentElement.classList.remove('premium-disabled');
            }
        }

        // Toggle controls
        const toggle = (el, disabled, placeholderText) => {
            if (!el) return;
            el.disabled = disabled;
            if (placeholderText) el.placeholder = placeholderText;
        };

        if (this.premiumLocked) {
            toggle(serviceFilter, true, 'Premium feature: service/IP targeting coming soon');
            toggle(regionFilter, true, 'Premium feature: region/IP targeting coming soon');
            if (selectAllBtn) selectAllBtn.disabled = true;
            if (clearAllBtn) clearAllBtn.disabled = true;
        } else {
            toggle(serviceFilter, false);
            toggle(regionFilter, false);
            if (selectAllBtn) selectAllBtn.disabled = false;
            if (clearAllBtn) clearAllBtn.disabled = false;
        }
    }

    async startUpgrade() {
        const emailInput = document.getElementById('email');
        if (!emailInput || !emailInput.value) {
            this.showError('Enter your email to start the upgrade.');
            return;
        }
        const email = emailInput.value.trim();
        try {
            const res = await fetch(`${this.apiBaseUrl}/api/upgrade`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            const data = await res.json();
            if (res.ok && data.success && data.checkout_url) {
                window.location.href = data.checkout_url;
            } else {
                this.showError(data.error || 'Upgrade is not available yet.');
            }
        } catch (err) {
            console.error('Upgrade start failed', err);
            this.showError('Upgrade request failed. Please try again.');
        }
    }

    showSuccess(message) {
        const messageElement = document.getElementById('formMessage');
        messageElement.className = 'form-message success';
        messageElement.textContent = message;
        messageElement.style.display = 'block';
        
        setTimeout(() => {
            messageElement.style.display = 'none';
        }, 5000);
    }

    showError(message) {
        const messageElement = document.getElementById('formMessage');
        messageElement.className = 'form-message error';
        messageElement.textContent = message;
        messageElement.style.display = 'block';
        
        setTimeout(() => {
            messageElement.style.display = 'none';
        }, 5000);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    new SubscriptionManager();
});
