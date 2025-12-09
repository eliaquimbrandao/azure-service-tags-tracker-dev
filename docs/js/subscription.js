/**
 * Subscription Page JavaScript
 * Handles email subscription form with service and region filtering
 */

class SubscriptionManager {
    constructor() {
        this.services = [];
        this.selectedServices = new Set();
        this.selectedRegions = new Set();
        this.selectedIpQueries = new Set();
        this.targetSearchResults = [];
        this.currentCategory = 'all';
        this.searchTerm = '';
        this.currentPage = 1;
        this.itemsPerPage = 50;
        // Show CTA state while upgrading
        const submitBtn = document.getElementById('subscribeBtn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Opening Premium Checkout...</span>';
        }
        this.allRegions = this.getAllAzureRegions();
        this.premiumLocked = true; // Filtered targeting is premium-only for now
        this.planStatus = { plan: 'free', status: 'inactive', expires_at: null };
        this.devPremiumOverride = this.getPremiumOverride();
        // API endpoint - update this when deploying to Vercel
        this.apiBaseUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'http://localhost:3000'  // Local development
            : 'https://azure-service-tags-tracker-dev.vercel.app';  // Production Vercel API
        // Apply dev override before initializing UI
        if (this.devPremiumOverride) {
            this.planStatus = { plan: 'premium', status: 'active', expires_at: null };
            this.premiumLocked = false;
        }

        this.init();
    }

    getPremiumOverride() {
        const params = new URLSearchParams(window.location.search || '');
        // Explicit off switch
        if (params.get('premium') === '0' || params.get('devPremium') === '0') return false;
        // Force on via query
        if (params.get('premium') === '1' || params.get('devPremium') === '1') return true;
        if (window.localStorage && window.localStorage.getItem('premium_override') === '1') return true;
        return false;
    }

    setPremiumOverride(enabled) {
        this.devPremiumOverride = enabled;
        if (window.localStorage) {
            if (enabled) {
                window.localStorage.setItem('premium_override', '1');
            } else {
                window.localStorage.removeItem('premium_override');
            }
        }
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
        // Apply status to reflect dev override/premium unlock before first render
        this.applyPlanStatus();
        // If email prefilled, validate plan status on load
        const emailInput = document.getElementById('email');
        if (emailInput && emailInput.value) {
            this.checkPlanStatus();
        }
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
            this.buildIpPrefixCache();
        } catch (error) {
            console.error('Error loading services:', error);
            this.showError('Failed to load services. Please try again later.');
        }
    }

    buildIpPrefixCache() {
        const seen = new Set();
        this.ipPrefixes = [];
        this.services.forEach(svc => {
            const prefixes = this.normalizeServicePrefixes(svc);
            prefixes.forEach(p => {
                const lower = p.toLowerCase();
                if (seen.has(lower)) return;
                seen.add(lower);
                this.ipPrefixes.push({ raw: p, lower });
            });
        });
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
        const premiumIdGroup = document.getElementById('premiumIdGroup');
        radioButtons.forEach(radio => {
            radio.addEventListener('change', (e) => {
                const filterSection = document.getElementById('filterSection');
                const submitBtn = document.getElementById('subscribeBtn');
                if (e.target.value === 'filtered') {
                    if (this.premiumLocked) {
                        if (submitBtn) {
                            submitBtn.disabled = false;
                            submitBtn.innerHTML = '<span class="btn-icon">💎</span><span class="btn-text">Upgrade to Premium ($1/mo)</span>';
                        }
                        if (filterSection) filterSection.style.display = 'none';
                        return; // Keep radio selected but require upgrade on submit
                    }
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<span class="btn-icon">💎</span><span class="btn-text">Subscribe to Premium ($1/mo)</span>';
                    }
                    if (filterSection) filterSection.style.display = 'block';
                    if (premiumIdGroup) premiumIdGroup.style.display = this.premiumLocked ? 'none' : 'block';
                } else {
                    if (submitBtn) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<span class="btn-icon">📧</span><span class="btn-text">Subscribe to All Changes (Free)</span>';
                    }
                    if (filterSection) filterSection.style.display = 'none';
                    if (premiumIdGroup) premiumIdGroup.style.display = 'none';
                }
            });
        });

        // Cache filters/buttons for later toggle updates
        this.serviceFilterEl = document.getElementById('serviceFilter');
        this.regionFilterEl = document.getElementById('regionFilter');
        this.selectAllBtnEl = document.getElementById('selectAllBtn');
        this.clearAllBtnEl = document.getElementById('clearAllBtn');
        this.premiumIdEl = document.getElementById('premiumId');
        this.targetSearchEl = document.getElementById('targetSearch');
        this.targetSearchResultsEl = document.getElementById('targetSearchResults');
        this.selectedTargetsEl = document.getElementById('selectedTargets');

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

        // Service filter search (supports IP queries)
        if (this.serviceFilterEl) {
            this.serviceFilterEl.addEventListener('input', (e) => {
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
        const regionFilter = this.regionFilterEl;
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
        const selectAllBtn = this.selectAllBtnEl;
        const clearAllBtn = this.clearAllBtnEl;
        
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

        // Unified target search (service/region/IP)
        if (this.targetSearchEl) {
            let targetSearchTimeout;
            this.targetSearchEl.addEventListener('input', (e) => {
                const term = e.target.value;
                clearTimeout(targetSearchTimeout);
                targetSearchTimeout = setTimeout(() => this.handleTargetSearch(term), 200);
            });

            this.targetSearchEl.addEventListener('focus', (e) => {
                if (e.target.value) {
                    this.handleTargetSearch(e.target.value);
                }
            });
        }

        // Hide dropdown when clicking outside
        if (this.targetSearchResultsEl) {
            document.addEventListener('click', (e) => {
                if (!this.targetSearchResultsEl.contains(e.target) && !this.targetSearchEl?.contains(e.target)) {
                    this.targetSearchResultsEl.style.display = 'none';
                }
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
            const total = this.selectedServices.size + this.selectedRegions.size + this.selectedIpQueries.size;
            countElement.textContent = `${total} target${total !== 1 ? 's' : ''}`;
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
        this.selectedIpQueries.clear();
        // Uncheck all visible checkboxes
        const checkboxes = document.querySelectorAll('.service-item input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        this.updateSelectedCount();
        this.renderSelectedTargets();
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
        return this.isIPv4(t) || this.isIPv4Cidr(t) || this.isIPv6(t) || this.isIPv6Cidr(t);
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

    isIPv6(ip) {
        return Boolean(this.parseIPv6(ip));
    }

    isIPv6Cidr(cidr) {
        const parts = cidr.split('/');
        if (parts.length !== 2) return false;
        const [ip, prefix] = parts;
        const prefixNum = Number(prefix);
        return this.isIPv6(ip) && Number.isInteger(prefixNum) && prefixNum >= 0 && prefixNum <= 128;
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

    parseIPv6(ip) {
        if (!ip || typeof ip !== 'string') return null;
        const lower = ip.toLowerCase();
        if ((lower.match(/::/g) || []).length > 1) return null;
        const [head, tail] = lower.split('::');
        const headSegs = head ? head.split(':').filter(Boolean) : [];
        const tailSegs = tail ? tail.split(':').filter(Boolean) : [];

        // Validate segments are hex and <= 4 chars
        const validSeg = (seg) => seg.length > 0 && seg.length <= 4 && /^[0-9a-f]{1,4}$/i.test(seg);
        if (!headSegs.every(validSeg)) return null;
        if (!tailSegs.every(validSeg)) return null;

        const total = headSegs.length + tailSegs.length;
        if (total > 8) return null;
        const fill = 8 - total;
        const fullSegs = [...headSegs, ...Array(fill).fill('0'), ...tailSegs].map(seg => parseInt(seg, 16));
        if (fullSegs.length !== 8) return null;

        return fullSegs;
    }

    ipv6ToBigInt(segs) {
        return segs.reduce((acc, seg) => (acc << 16n) + BigInt(seg), 0n);
    }

    ipInIPv6Cidr(ip, cidr) {
        if (!this.isIPv6(ip)) return false;
        if (!this.isIPv6Cidr(cidr)) return false;
        const [network, prefix] = cidr.split('/');
        const prefixBits = BigInt(Number(prefix));
        const ipSegs = this.parseIPv6(ip);
        const netSegs = this.parseIPv6(network);
        if (!ipSegs || !netSegs) return false;
        const ipBig = this.ipv6ToBigInt(ipSegs);
        const netBig = this.ipv6ToBigInt(netSegs);
        if (prefixBits === 0n) return true;
        const mask = (BigInt(-1) << (128n - prefixBits)) & ((1n << 128n) - 1n);
        return (ipBig & mask) === (netBig & mask);
    }

    serviceMatchesIp(service, searchTerm) {
        const prefixes = this.normalizeServicePrefixes(service);
        const term = searchTerm.trim();
        if (!prefixes.length) return false;

        // Exact CIDR match
        if (this.isIPv4Cidr(term)) {
            return prefixes.some(p => this.isIPv4Cidr(p) ? p === term : false);
        }
        if (this.isIPv6Cidr(term)) {
            const lowered = term.toLowerCase();
            return prefixes.some(p => this.isIPv6Cidr(p) ? p.toLowerCase() === lowered : false);
        }

        // IP match inside any CIDR
        if (this.isIPv4(term)) {
            return prefixes.some(p => {
                if (this.isIPv4Cidr(p)) return this.ipInCidr(term, p);
                if (this.isIPv4(p)) return p === term;
                return false;
            });
        }
        if (this.isIPv6(term)) {
            const loweredTerm = term.toLowerCase();
            return prefixes.some(p => {
                if (this.isIPv6Cidr(p)) return this.ipInIPv6Cidr(loweredTerm, p.toLowerCase());
                if (this.isIPv6(p)) return p.toLowerCase() === loweredTerm;
                return false;
            });
        }

        return false;
    }

    normalizeServicePrefixes(service) {
        if (!service || !service.properties) return [];
        const prefixes = service.properties.addressPrefixes || [];
        return prefixes.map(p => (typeof p === 'string' ? p.trim() : '')).filter(Boolean);
    }

    getRegionsForIp(searchTerm) {
        const regions = new Set();
        const term = searchTerm.trim();
        if (!term) return regions;

        this.services.forEach(service => {
            const regionId = ((service.properties && service.properties.region) || '').toLowerCase();
            if (!regionId) return;
            if (this.serviceMatchesIp(service, term)) {
                regions.add(regionId);
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

    handleTargetSearch(term) {
        if (!this.targetSearchResultsEl) return;
        if (this.premiumLocked) {
            this.targetSearchResultsEl.innerHTML = '<div class="region-dropdown-item no-results">Premium required to search targets.</div>';
            this.targetSearchResultsEl.style.display = 'block';
            return;
        }

        const query = (term || '').trim();
        if (!query) {
            this.targetSearchResultsEl.style.display = 'none';
            return;
        }

        const results = this.getTargetResults(query);
        this.renderTargetSearchResults(results, query);
    }

    getTargetResults(query) {
        const q = query.trim();
        const qLower = q.toLowerCase();
        const results = [];
        if (!qLower) return results;

        const isIpLike = this.isIpQuery(qLower) || /\d+\.\d+/.test(qLower);

        const addedServiceIds = new Set();
        const regionResults = [];
        const serviceResults = [];
        const ipResults = [];

        // IP-driven search first to surface exact matches
        if (isIpLike) {
            const matchedServices = this.services.filter(s => this.serviceMatchesIp(s, qLower));
            const serviceIds = matchedServices.map(s => s.id);
            results.push({
                type: 'ip',
                value: q,
                label: q,
                meta: matchedServices.length ? `Matches ${matchedServices.length} service${matchedServices.length !== 1 ? 's' : ''}` : 'IP query (no matching services yet)',
                services: serviceIds
            });

            matchedServices.slice(0, 8).forEach(s => {
                addedServiceIds.add(s.id);
                serviceResults.push({
                    type: 'service',
                    value: s.id,
                    label: s.name,
                    meta: s.properties?.region ? this.getRegionDisplayName(s.properties.region) : 'Service tag'
                });
            });

            // If the query isn't a full IP/CIDR, suggest prefix matches from known ranges
            const isFullIp = this.isIPv4(qLower) || this.isIPv4Cidr(qLower) || this.isIPv6(qLower) || this.isIPv6Cidr(qLower);
            if (!isFullIp && this.ipPrefixes && this.ipPrefixes.length) {
                const prefixHits = this.ipPrefixes
                    .filter(p => p.lower.includes(qLower))
                    .slice(0, 8);
                prefixHits.forEach(hit => {
                    ipResults.push({
                        type: 'ip',
                        value: hit.raw,
                        label: hit.raw,
                        meta: 'Prefix match'
                    });
                });
            }
        }

        // Region search (prioritize showing region before its services)
        const regionMatches = this.allRegions
            .filter(r => r.name.toLowerCase().includes(qLower) || r.id.toLowerCase().includes(qLower))
            .slice(0, 6);

        regionMatches.forEach(r => {
            regionResults.push({
                type: 'region',
                value: r.id,
                label: r.name,
                meta: 'Region'
            });

            // Add services that live in this region (limit to avoid overflow)
            const regionServices = this.services
                .filter(s => (s.properties?.region || '').toLowerCase() === r.id.toLowerCase())
                .slice(0, 5);
            regionServices.forEach(s => {
                if (addedServiceIds.has(s.id)) return;
                addedServiceIds.add(s.id);
                serviceResults.push({
                    type: 'service',
                    value: s.id,
                    label: s.name,
                    meta: this.getRegionDisplayName(r.id)
                });
            });
        });

        // Service name search (after region priority)
        const serviceMatches = this.services
            .filter(s => s.name.toLowerCase().includes(qLower) || s.id.toLowerCase().includes(qLower))
            .slice(0, 8);
        serviceMatches.forEach(s => {
            if (addedServiceIds.has(s.id)) return;
            addedServiceIds.add(s.id);
            serviceResults.push({
                type: 'service',
                value: s.id,
                label: s.name,
                meta: s.properties?.region ? this.getRegionDisplayName(s.properties.region) : 'Service tag'
            });
        });

        // Order: IP result (if any), then regions, then services
        // For all searches, append any extra IP suggestions, then regions, then services (IP query entry stays at the top)
        results.push(...ipResults);
        results.push(...regionResults);
        results.push(...serviceResults);

        return results;
    }

    renderTargetSearchResults(results, query) {
        if (!this.targetSearchResultsEl) return;

        if (!results.length) {
            this.targetSearchResultsEl.innerHTML = `<div class="region-dropdown-item no-results">No matches for "${this.escapeHtml(query)}"</div>`;
            this.targetSearchResultsEl.style.display = 'block';
            return;
        }

        const itemsHtml = results.map((item, idx) => {
            const meta = item.meta ? `<span class="region-id">${this.escapeHtml(item.meta)}</span>` : '';
            return `
                <div class="region-dropdown-item" data-idx="${idx}" data-type="${item.type}" data-value="${this.escapeHtml(item.value)}">
                    <span class="region-name">${this.escapeHtml(item.label)}</span>
                    ${meta}
                </div>
            `;
        }).join('');

        this.targetSearchResults = results;
        this.targetSearchResultsEl.innerHTML = itemsHtml;
        this.targetSearchResultsEl.style.display = 'block';

        this.targetSearchResultsEl.querySelectorAll('.region-dropdown-item').forEach(el => {
            el.addEventListener('click', () => {
                const idx = Number(el.getAttribute('data-idx'));
                const picked = this.targetSearchResults[idx];
                if (picked) {
                    this.addTargetSelection(picked);
                }
            });
        });
    }

    addTargetSelection(item) {
        if (!item) return;
        if (item.type === 'service') {
            this.selectedServices.add(item.value);
        } else if (item.type === 'region') {
            this.selectedRegions.add(item.value);
        } else if (item.type === 'ip') {
            // IP selections are tracked as standalone queries; do not auto-add services
            this.selectedIpQueries.add(item.value);
        }

        if (this.targetSearchEl) {
            this.targetSearchEl.value = '';
        }
        if (this.targetSearchResultsEl) {
            this.targetSearchResultsEl.style.display = 'none';
        }

        this.renderSelectedTargets();
        this.updateSelectedCount();
    }

    removeTargetSelection(type, value) {
        if (type === 'service') {
            this.selectedServices.delete(value);
        } else if (type === 'region') {
            this.selectedRegions.delete(value);
        } else if (type === 'ip') {
            this.selectedIpQueries.delete(value);
        }
        this.renderSelectedTargets();
        this.updateSelectedCount();
    }

    renderSelectedTargets() {
        if (!this.selectedTargetsEl) return;
        const items = [];

        this.selectedIpQueries.forEach(ip => {
            items.push({ type: 'ip', value: ip, label: ip });
        });

        this.selectedRegions.forEach(regionId => {
            items.push({ type: 'region', value: regionId, label: this.getRegionDisplayName(regionId) });
        });

        this.selectedServices.forEach(serviceId => {
            items.push({ type: 'service', value: serviceId, label: this.getServiceName(serviceId) });
        });

        if (!items.length) {
            this.selectedTargetsEl.style.display = 'none';
            this.selectedTargetsEl.innerHTML = '';
            return;
        }

        this.selectedTargetsEl.style.display = 'flex';
        this.selectedTargetsEl.innerHTML = items.map(item => `
            <div class="region-tag" data-type="${item.type}" data-value="${this.escapeHtml(item.value)}">
                <span class="region-tag-name">${this.escapeHtml(item.label)}</span>
                <button type="button" class="region-tag-remove" data-type="${item.type}" data-value="${this.escapeHtml(item.value)}">×</button>
            </div>
        `).join('');

        this.selectedTargetsEl.querySelectorAll('.region-tag-remove').forEach(btn => {
            btn.addEventListener('click', () => {
                this.removeTargetSelection(btn.dataset.type, btn.dataset.value);
            });
        });
    }

    getServiceName(serviceId) {
        const svc = this.services.find(s => s.id === serviceId || s.name === serviceId);
        return svc ? svc.name : serviceId;
    }

    getRegionDisplayName(regionId) {
        if (!regionId) return 'Global';
        const region = this.allRegions.find(r => r.id.toLowerCase() === regionId.toLowerCase());
        if (region) return region.name;
        return regionId;
    }

    async handleSubmit() {
        const email = document.getElementById('email').value;
        const subscriptionType = document.querySelector('input[name="subscriptionType"]:checked').value;
        const premiumId = (this.premiumIdEl || document.getElementById('premiumId'))?.value.trim() || '';
        
        const subscriptionData = {
            email: email,
            subscriptionType: subscriptionType,
            selectedServices: subscriptionType === 'filtered' ? Array.from(this.selectedServices) : [],
            selectedRegions: subscriptionType === 'filtered' ? Array.from(this.selectedRegions) : [],
            user_id: subscriptionType === 'filtered' ? premiumId : undefined,
            ip_queries: subscriptionType === 'filtered' ? Array.from(this.selectedIpQueries) : []
        };

        // Validation and premium gating
        if (subscriptionType === 'filtered') {
            // Re-validate plan before submitting
            const premiumOK = await this.checkPlanStatus();
            if (!premiumOK) {
                this.premiumLocked = true;
                this.applyPlanStatus();
                this.showError('Premium is required for targeted alerts. Use your premium email/ID or upgrade first.');
                return;
            }
            if (!premiumId) {
                this.showError('Add a Premium ID or username so we can tie your filtered alerts.');
                const premiumInput = this.premiumIdEl || document.getElementById('premiumId');
                if (premiumInput) premiumInput.focus();
                return;
            }
            const hasTargets = (this.selectedServices.size + this.selectedRegions.size + this.selectedIpQueries.size) > 0;
            if (!hasTargets) {
                this.showError('Select at least one target (service, region, or IP) for premium alerts.');
                return;
            }
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
                    this.selectedIpQueries.clear();
                    this.updateSelectedCount();
                    document.getElementById('filterSection').style.display = 'none';
                    const premiumInput = this.premiumIdEl || document.getElementById('premiumId');
                    if (premiumInput) premiumInput.value = '';
                    this.renderSelectedTargets();
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
                return this.isPremiumActive();
            }
        } catch (err) {
            console.error('Plan status check failed', err);
        }
        // Default to locked if status cannot be verified
        this.planStatus = { plan: 'free', status: 'inactive', expires_at: null };
        this.applyPlanStatus();
        return false;
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

        // Enable upgrade button for non-premium users
        if (upgradeBtn) {
            upgradeBtn.disabled = false;
        }

        const isPremium = this.devPremiumOverride || (this.planStatus.plan === 'premium' && this.planStatus.status === 'active');
        if (statusWrap && statusText) {
            statusWrap.style.display = 'flex';
            if (isPremium) {
                statusText.textContent = 'Premium active — targeted filters unlocked.';
            } else {
                statusText.textContent = 'Free plan — choose Premium to upgrade and unlock targeted filters ($1/mo).';
            }
        }

        this.premiumLocked = !isPremium;
        if (filteredRadio && !this.premiumLocked) {
            filteredRadio.parentElement.classList.remove('premium-disabled');
        }

        // Reset submit button state based on plan
        const submitBtn = document.getElementById('subscribeBtn');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span class="btn-icon">📧</span><span class="btn-text">Subscribe to All Changes (Free)</span>';
        }

        // Sync UI controls and overlays with current lock state
        this.updatePremiumLockUI();
    }

    isPremiumActive() {
        return this.devPremiumOverride || (this.planStatus.plan === 'premium' && this.planStatus.status === 'active');
    }

    updatePremiumLockUI() {
        const locked = this.premiumLocked;
        const svc = this.serviceFilterEl || document.getElementById('serviceFilter');
        const reg = this.regionFilterEl || document.getElementById('regionFilter');
        const selectAllBtn = this.selectAllBtnEl || document.getElementById('selectAllBtn');
        const clearAllBtn = this.clearAllBtnEl || document.getElementById('clearAllBtn');
        const premiumId = document.getElementById('premiumId');
        const premiumIdGroup = document.getElementById('premiumIdGroup');
        const filterSection = document.getElementById('filterSection');
        const filteredRadio = document.querySelector('input[name="subscriptionType"][value="filtered"]');
        const targetSearch = this.targetSearchEl || document.getElementById('targetSearch');
        const targetResults = this.targetSearchResultsEl || document.getElementById('targetSearchResults');

        if (svc) {
            svc.disabled = locked;
            svc.placeholder = locked ? 'Premium feature: service/IP targeting coming soon' : 'Search services or IPs (e.g., Storage, 13.107.6.10)';
        }
        if (reg) {
            reg.disabled = locked;
            reg.placeholder = locked ? 'Premium feature: region/IP targeting coming soon' : 'Search regions or IPs (e.g., East US, 13.107.6.10)';
        }
        if (premiumId) premiumId.disabled = locked;
        if (premiumIdGroup) premiumIdGroup.style.display = locked ? 'none' : 'block';
        if (selectAllBtn) selectAllBtn.disabled = locked;
        if (clearAllBtn) clearAllBtn.disabled = locked;
        if (targetSearch) targetSearch.disabled = locked;
        if (targetResults && locked) targetResults.style.display = 'none';

        if (filterSection) {
            const filteredSelected = filteredRadio && filteredRadio.checked;
            filterSection.style.display = locked ? 'none' : (filteredSelected ? 'block' : 'none');
        }

        // When locked, force radio back to free
        if (locked && filteredRadio && filteredRadio.checked) {
            const freeRadio = document.querySelector('input[name="subscriptionType"][value="all"]');
            if (freeRadio) {
                freeRadio.checked = true;
            }
        }

        document.querySelectorAll('.premium-overlay').forEach(el => {
            el.style.display = locked ? 'flex' : 'none';
        });

        // Rerender services to show/hide list accordingly
        if (this.services && this.services.length) {
            this.renderServices();
        }
    }

    async startUpgrade() {
        const emailInput = document.getElementById('email');
        if (!emailInput || !emailInput.value) {
            this.showError('Enter your email to start the upgrade.');
            if (emailInput) emailInput.focus();
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
                if (data.waitlist_url) {
                    // Offer to open waitlist link in a new tab
                    window.open(data.waitlist_url, '_blank');
                    this.showError('Premium upgrade is not live yet. We opened the waitlist email for you.');
                } else {
                    this.showError(data.error || 'Upgrade is not available yet.');
                }
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
