// ui_handlers.js - CORRECTED with visible Skeleton Loader

export function getDOMElements() {
    return {
        // Auth & Main Containers
        loginRegisterContent: document.getElementById('login-register-content'),
        mainAppContent: document.getElementById('main-app-content'),
        loginForm: document.getElementById('loginForm'),
        registerForm: document.getElementById('registerForm'),
        loginUsername: document.getElementById('loginUsername'),
        loginPassword: document.getElementById('loginPassword'),
        registerUsername: document.getElementById('registerUsername'),
        registerPassword: document.getElementById('registerPassword'),
        registerConfirmPassword: document.getElementById('registerConfirmPassword'),
        showRegister: document.getElementById('showRegister'),
        showLogin: document.getElementById('showLogin'),
        logoutBtn: document.getElementById('logoutBtn'),
        navbarUsername: document.getElementById('navbarUsername'),
        settingsUsername: document.getElementById('settingsUsername'),
        
        // Navigation & Header
        navLinks: document.querySelectorAll('.sidebar-link'),
        pageTitle: document.getElementById('page-title'),

        // Dashboard elements
        dashboardLoader: document.getElementById('dashboard-loader'),
        dashboardContent: document.getElementById('dashboard-content'),
        dashboardWelcome: document.getElementById('dashboard-welcome'),
        dashboardCtaBtn: document.getElementById('dashboard-cta-btn'),
        dashboardWelcomeUser: document.getElementById('dashboardWelcomeUser'),
        dashboardWelcomeLocation: document.getElementById('dashboardWelcomeLocation'),
        dashboardReportDate: document.getElementById('dashboard-report-date'),
        dashboardReportCrop: document.getElementById('dashboard-report-crop'),
        dashboardPriceCrop: document.getElementById('dashboard-price-crop'),
        dashboardPriceValue: document.getElementById('dashboard-price-value'),
        dashboardSoilType: document.getElementById('dashboardSoilType'),
        dashboardWeatherLocation: document.getElementById('dashboardWeatherLocation'),
        dashboardCurrentTemp: document.getElementById('dashboardCurrentTemp'),
        dashboardCurrentDesc: document.getElementById('dashboardCurrentDesc'),
        mandiPriceChart: document.getElementById('mandiPriceChart'),
        
        // Analyze Crop
        analyzeCropBtn: document.getElementById('analyzeCropBtn'),
        cropImageUpload: document.getElementById('cropImageUpload'),
        cropImagePreview: document.getElementById('cropImagePreview'),
        cropResultsDisplay: document.getElementById('cropResultsDisplay'),

        // Analyze Field
        analyzeFieldBtn: document.getElementById('analyzeFieldBtn'),
        soilImageUpload: document.getElementById('soilImageUpload'),
        soilImagePreview: document.getElementById('soilImagePreview'), // <-- ADD THIS LINE
        latitude: document.getElementById('latitude'),
        longitude: document.getElementById('longitude'),
        getLocationBtn: document.getElementById('getLocationBtn'),
        lastCrop: document.getElementById('lastCrop'),
        fieldResultsDisplay: document.getElementById('fieldResultsDisplay'),
        
        // Fertilizer Elements
        fertilizerReportSelect: document.getElementById('fertilizerReportSelect'),
        getFertilizerPlanBtn: document.getElementById('getFertilizerPlanBtn'),
        fertilizerResultsDisplay: document.getElementById('fertilizerResultsDisplay'),
        
        // Price Info
        priceState: document.getElementById('price_state'),
        priceDistrict: document.getElementById('price_district'),
        priceCrop: document.getElementById('price_crop'),
        priceArea: document.getElementById('price_area'),
        findPriceBtn: document.getElementById('findPriceBtn'),
        priceResultsDisplay: document.getElementById('priceResultsDisplay'),

        // Reports
        saveReportBtn: document.getElementById('saveReportBtn'),
        myReportsContent: document.getElementById('myReportsContent'),

        // Settings page elements
        changePasswordForm: document.getElementById('changePasswordForm'),
        currentPassword: document.getElementById('currentPassword'),
        newPassword: document.getElementById('newPassword'),
        confirmNewPassword: document.getElementById('confirmNewPassword'),
        changePasswordBtn: document.getElementById('changePasswordBtn'),
        deleteAccountBtn: document.getElementById('deleteAccountBtn'),
    };
}

export function showMessage(message, type = 'info') {
    const container = document.getElementById('messageBox-container') || document.body;
    const messageBox = document.createElement('div');
    messageBox.className = `fixed top-5 left-1/2 -translate-x-1/2 p-4 rounded-lg text-white font-semibold shadow-lg transition-all duration-300 transform -translate-y-20 opacity-0 z-50`;
    const colors = { info: 'bg-blue-500', success: 'bg-green-500', warning: 'bg-yellow-500', error: 'bg-red-500' };
    messageBox.classList.add(colors[type]);
    messageBox.textContent = message;
    container.appendChild(messageBox);
    setTimeout(() => { messageBox.classList.replace('-translate-y-20', 'translate-y-0'); messageBox.classList.replace('opacity-0', 'opacity-100'); }, 10);
    setTimeout(() => {
        messageBox.classList.replace('translate-y-0', '-translate-y-20');
        messageBox.classList.replace('opacity-100', 'opacity-0');
        setTimeout(() => container.removeChild(messageBox), 300);
    }, 3500);
}

export function showSection(sectionId) {
    document.querySelectorAll('.sidebar-link').forEach(link => link.classList.remove('active'));
    const activeLink = document.querySelector(`.sidebar-link[data-page="${sectionId}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }

    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active');
    }
}

export function toggleAuthForms(showLogin) {
    document.getElementById('main-app-content').style.display = 'none';
    const authContainer = document.getElementById('login-register-content');
    if (authContainer) authContainer.style.display = 'block';

    document.getElementById('loginFormContainer').style.display = showLogin ? 'block' : 'none';
    document.getElementById('registerFormContainer').style.display = showLogin ? 'none' : 'block';
}

export function setButtonLoading(button, isLoading) {
    if (!button) return;
    const textSpan = button.querySelector('span:not(.loader)');
    const loaderSpan = button.querySelector('.loader');
    button.disabled = isLoading;
    if (textSpan) textSpan.style.display = isLoading ? 'none' : 'inline';
    if (loaderSpan) loaderSpan.style.display = isLoading ? 'inline-block' : 'none';
}

// --- THIS IS THE FIX ---
// The getLoaderHTML function is updated to return skeleton bars without the extra container.
export function getLoaderHTML(text) {
    if (text.toLowerCase().includes('dashboard')) {
        return `
            <div class="text-left py-4 w-full">
                <div class="skeleton skeleton-title w-1/3 mb-4"></div>
                <div class="skeleton h-48 mb-6 rounded-xl"></div>
                <div class="skeleton skeleton-title w-1/4 mb-4"></div>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div class="skeleton h-32 rounded-xl"></div>
                    <div class="skeleton h-32 rounded-xl"></div>
                    <div class="skeleton h-32 rounded-xl"></div>
                    <div class="skeleton h-32 rounded-xl"></div>
                </div>
            </div>
        `;
    }

    // This generic skeleton now has a wrapper to ensure it's treated as a single centered block,
    // but the wrapper has no background, so the gray skeleton bars are visible against the parent card.
    return `
        <div class="w-full text-left">
            <div class="skeleton skeleton-title w-1/3 mb-4"></div>
            <div class="skeleton skeleton-text w-full"></div>
            <div class="skeleton skeleton-text w-full"></div>
            <div class="skeleton skeleton-text w-3/4"></div>
            <div class="skeleton h-24 mt-6"></div>
        </div>
    `;
}


export function displayImagePreview(fileInput, previewContainer) {
    if (!previewContainer) return;
    previewContainer.innerHTML = '';
    const file = fileInput.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = document.createElement('img');
            img.src = e.target.result;
            img.alt = 'Image Preview';
            img.className = 'max-w-xs mx-auto h-auto rounded-lg shadow-md max-h-48';
            previewContainer.appendChild(img);
        };
        reader.readAsDataURL(file);
    }
}

export function updateNavbarUsername(username) {
    const el = document.getElementById('navbarUsername');
    if(el) el.textContent = `${username}`;
}

export function updateSettingsUsername(username) {
    const el = document.getElementById('settingsUsername');
    if(el) el.textContent = username;
}

export function animateContentSwap(container, newContentOrFunction) {
    if (!container) return;

    // 1. Start the fade-out
    container.style.opacity = '0';

    // 2. Wait for the fade-out animation (300ms) to finish
    setTimeout(() => {
        // 3. Update the content *after* it's invisible
        if (typeof newContentOrFunction === 'string') {
            container.innerHTML = newContentOrFunction;
        } else if (typeof newContentOrFunction === 'function') {
            newContentOrFunction(container);
        }
        
        // 4. Fade the new content back in
        container.style.opacity = '1';
    }, 300); // This duration MUST match the CSS transition duration
}