// script.js - FINAL CORRECTED VERSION

import * as UI from './ui_handlers.js';
import * as API from './api_client.js';
import * as ReportFormatter from './report_formatter.js';
import { initI18n, getCurrentLanguage } from './i18n.js';

document.addEventListener('DOMContentLoaded', () => {
    console.log("Kisan Drishti scripts initializing...");
    
    initI18n();

    const elements = UI.getDOMElements();
    const chatWidget = document.getElementById('drishti-chat-widget');
    const getCurrentTime = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    let lastAnalyzedFieldReport = null;
    let locationData = null;
    let mandiChartInstance = null;

    const dashboardTranslations = {
        en: {
            welcome: (user) => `Welcome Back, ${user}!`,
            overview: (loc) => `Your Personalized Farm Overview for ${loc}`,
            on_date: (date) => `On ${date}`,
            for_crop: (crop) => `(for ${crop})`,
            in_location: (loc) => `in ${loc}`
        },
        hi: {
            welcome: (user) => `${user}, आपका स्वागत है!`,
            overview: (loc) => `${loc} के लिए आपका व्यक्तिगत फार्म अवलोकन`,
            on_date: (date) => `दिनांक ${date} को`,
            for_crop: (crop) => `(${crop} के लिए)`,
            in_location: (loc) => `${loc} में`
        }
    };

    async function loadDashboardData() {
        elements.dashboardLoader.innerHTML = UI.getLoaderHTML('Loading Your Dashboard...');
        elements.dashboardLoader.classList.remove('hidden');
        elements.dashboardContent.classList.add('hidden');
        elements.dashboardWelcome.classList.add('hidden');
        
        try {
            const data = await API.getDashboardSummary(getCurrentLanguage());
            if (data.has_data) {
                renderDashboard(data);
            } else {
                showDashboardWelcome();
            }
        } catch(error) {
            UI.showMessage(error.message, 'error');
            elements.dashboardLoader.innerHTML = `<p class="text-red-600 p-4 text-center">${error.message}</p>`;
        }
    }

    function renderDashboard(data) {
        elements.dashboardLoader.classList.add('hidden');
        elements.dashboardWelcome.classList.add('hidden');
        elements.dashboardContent.classList.remove('hidden');

        const lang = getCurrentLanguage();
        const T = dashboardTranslations[lang];

        const welcomeBanner = document.querySelector('.hero-text h3');
        const overviewBanner = document.querySelector('.hero-text p');
        if (welcomeBanner) welcomeBanner.innerHTML = T.welcome(data.username);
        if (overviewBanner) overviewBanner.innerHTML = T.overview(data.location);

        if (elements.dashboardReportDate) elements.dashboardReportDate.textContent = T.on_date(data.last_report.date);
        if (elements.dashboardReportCrop) elements.dashboardReportCrop.textContent = data.last_report.top_crop_recommended;
        
        if (elements.dashboardPriceCrop) elements.dashboardPriceCrop.textContent = T.for_crop(data.mandi_price.crop || 'N/A');
        if (elements.dashboardPriceValue) elements.dashboardPriceValue.textContent = data.mandi_price.price ? `₹${data.mandi_price.price}` : 'N/A';
        
        if (elements.dashboardSoilType) elements.dashboardSoilType.textContent = data.soil_type || 'N/A';
        
        if (elements.dashboardWeatherLocation) elements.dashboardWeatherLocation.textContent = T.in_location(data.location);
        const temp = parseFloat(data.current_weather?.temperature);
        if (elements.dashboardCurrentTemp) {
            elements.dashboardCurrentTemp.textContent = !isNaN(temp) ? `${Math.round(temp)}°C` : 'N/A';
        }
        if (elements.dashboardCurrentDesc) {
            elements.dashboardCurrentDesc.textContent = data.current_weather?.description || 'N/A';
        }
        
        renderMandiChart(elements.mandiPriceChart, data.price_chart);
    }
    
    document.addEventListener('language-changed', () => {
        console.log('Language change detected, checking active page...');
        const activeSection = document.querySelector('.content-section.active');
        
        if (activeSection && activeSection.id === 'dashboardSection') {
            console.log('Dashboard is active, reloading data...');
            loadDashboardData();
        }
    });

    function initializeMainApp(username) {
        elements.mainAppContent.style.display = 'flex'; 
        if (chatWidget) chatWidget.style.display = 'block';
        UI.updateNavbarUsername(username);
        UI.updateSettingsUsername(username);
        UI.showSection('dashboardSection');
        attachMainAppEventListeners();
        initializeLocationDropdowns();
        loadDashboardData();
    }

    async function checkAuthenticationAndInit() {
        try {
            const authStatus = await API.checkAuthStatus();
            if (authStatus && authStatus.isAuthenticated) {
                initializeMainApp(authStatus.username);
            } else {
                window.location.href = '/';
            }
        } catch (error) {
            console.error("Auth check failed, redirecting to landing page.", error);
            window.location.href = '/';
        }
    }

    async function handleLogin(event) {
        event.preventDefault();
        UI.setButtonLoading(event.target.querySelector('button'), true);
        const username = elements.loginUsername.value;
        const password = elements.loginPassword.value;
        if (!username || !password) {
            UI.setButtonLoading(event.target.querySelector('button'), false);
            return UI.showMessage('Please enter both username and password.', 'warning');
        }
        try {
            const data = await API.loginUser(username, password);
            window.location.href = '/app';
        } catch (error) {
            UI.showMessage(error.message, 'error');
        } finally {
            UI.setButtonLoading(event.target.querySelector('button'), false);
        }
    }

    async function handleRegister(event) {
        event.preventDefault();
        UI.setButtonLoading(event.target.querySelector('button'), true);
        const username = elements.registerUsername.value;
        const password = elements.registerPassword.value;
        const confirmPassword = elements.registerConfirmPassword.value;

        if (!username || !password || !confirmPassword) {
            UI.setButtonLoading(event.target.querySelector('button'), false);
            return UI.showMessage('Please fill in all fields.', 'warning');
        }
        if (password !== confirmPassword) {
            UI.setButtonLoading(event.target.querySelector('button'), false);
            return UI.showMessage('Passwords do not match.', 'error');
        }
        
        try {
            const data = await API.registerUser(username, password);
            window.location.href = '/app';
        } catch (error) {
            UI.showMessage(error.message, 'error');
        } finally {
            UI.setButtonLoading(event.target.querySelector('button'), false);
        }
    }

    async function handleLogout() {
        try { 
            await API.logoutUser(); 
            window.location.href = '/';
        } catch (error) { UI.showMessage(error.message, 'error'); }
    }
    
    async function handleChangePassword(event) {
        event.preventDefault();
        const { currentPassword, newPassword, confirmNewPassword, changePasswordBtn } = elements;
        if (newPassword.value !== confirmNewPassword.value) {
            return UI.showMessage("New passwords do not match.", 'error');
        }
        UI.setButtonLoading(changePasswordBtn, true);
        try {
            const data = await API.changePassword(currentPassword.value, newPassword.value);
            UI.showMessage(data.message, 'success');
            elements.changePasswordForm.reset();
        } catch (error) {
            UI.showMessage(error.message, 'error');
        } finally {
            UI.setButtonLoading(changePasswordBtn, false);
        }
    }

    async function handleDeleteAccount() {
        if (confirm("Are you sure you want to delete your account? This action is permanent and cannot be undone.")) {
            UI.setButtonLoading(elements.deleteAccountBtn, true);
            try {
                const data = await API.deleteAccount();
                UI.showMessage(data.message, 'success');
                setTimeout(() => window.location.reload(), 1500);
            } catch (error) {
                UI.showMessage(error.message, 'error');
                UI.setButtonLoading(elements.deleteAccountBtn, false);
            }
        }
    }

    function showDashboardWelcome() {
        elements.dashboardLoader.classList.add('hidden');
        elements.dashboardContent.classList.add('hidden');
        elements.dashboardWelcome.classList.remove('hidden');
    }

    function renderForecast(forecastData) {
        if (!elements.forecastContainer) return;
        elements.forecastContainer.innerHTML = '';
        if (!forecastData || forecastData.length === 0) {
            elements.forecastContainer.innerHTML = `<p class="col-span-full text-gray-500">Forecast data not available.</p>`;
            return;
        }
        forecastData.forEach(day => {
            const dayHtml = `<div class="bg-gray-50 p-3 rounded-lg"><p class="font-semibold text-sm">${day.day_name}</p><img src="https://openweathermap.org/img/wn/${day.icon}@2x.png" alt="weather icon" class="mx-auto my-1 h-12 w-12"><p class="font-medium">${Math.round(day.temp_max)}° / ${Math.round(day.temp_min)}°</p></div>`;
            elements.forecastContainer.innerHTML += dayHtml;
        });
    }
    
    function renderMandiChart(canvas, chartData) {
        if (mandiChartInstance) mandiChartInstance.destroy();
        if (!canvas) return;
        mandiChartInstance = new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: { labels: chartData.labels, datasets: [{ label: 'Avg. Price (₹/Quintal)', data: chartData.prices, backgroundColor: 'rgba(16, 185, 129, 0.6)', borderColor: 'rgba(16, 185, 129, 1)', borderWidth: 1, borderRadius: 5, }] },
            options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: false } } }
        });
    }

    async function handleAnalyzeCrop() {
        if (!elements.cropImageUpload.files[0]) return UI.showMessage('Please upload a crop image.', 'warning');

        UI.setButtonLoading(elements.analyzeCropBtn, true);
        elements.cropResultsDisplay.innerHTML = UI.getLoaderHTML('Analyzing Crop Health...');

        const formData = new FormData();
        formData.append('image', elements.cropImageUpload.files[0]);
        try {
            const data = await API.analyzeCrop(formData);
            const resultsHtml = ReportFormatter.displayCropAnalysis(data.result);
            UI.animateContentSwap(elements.cropResultsDisplay, resultsHtml);
        } catch (error) {
            UI.showMessage(error.message, 'error');
            elements.cropResultsDisplay.innerHTML = `<p class="text-red-600 text-center">${error.message}</p>`;
        } finally {
            UI.setButtonLoading(elements.analyzeCropBtn, false);
        }
    }

    async function handleAnalyzeField() {
        if (!elements.latitude.value || !elements.longitude.value) return UI.showMessage('Please provide latitude and longitude.', 'warning');
        if (!elements.soilImageUpload.files[0]) return UI.showMessage('A soil image is required for this analysis.', 'warning');
        
        UI.setButtonLoading(elements.analyzeFieldBtn, true);
        elements.fieldResultsDisplay.innerHTML = UI.getLoaderHTML('Analyzing Field Conditions...');
        
        const formData = new FormData();
        formData.append('latitude', elements.latitude.value);
        formData.append('longitude', elements.longitude.value);
        formData.append('lastCrop', elements.lastCrop.value);
        formData.append('image', elements.soilImageUpload.files[0]);
        formData.append('lang', getCurrentLanguage());

        try {
            const report = await API.analyzeField(formData);
            const reportHtml = ReportFormatter.displayFieldReport(report, getCurrentLanguage());
            UI.animateContentSwap(elements.fieldResultsDisplay, reportHtml);
            lastAnalyzedFieldReport = report;
            elements.saveReportBtn.style.display = 'block';
        } catch (error) {
            UI.showMessage(error.message, 'error');
            elements.fieldResultsDisplay.innerHTML = `<p class="text-red-600 text-center">${error.message}</p>`;
        } finally {
            UI.setButtonLoading(elements.analyzeFieldBtn, false);
        }
    }

    async function handleSaveReport() {
        if (!lastAnalyzedFieldReport) return UI.showMessage('No field report to save.', 'warning');
        UI.setButtonLoading(elements.saveReportBtn, true);
        try {
            const data = await API.saveReport(lastAnalyzedFieldReport);
            UI.showMessage(data.message, 'success');
            lastAnalyzedFieldReport = null;
            elements.saveReportBtn.style.display = 'none';
        } catch (error) {
            UI.showMessage(error.message, 'error');
        } finally {
            UI.setButtonLoading(elements.saveReportBtn, false);
        }
    }
    
    async function handleGetMandiPrices() {
        const { priceState, priceDistrict, priceCrop, priceArea, findPriceBtn, priceResultsDisplay } = elements;
        if (!priceState.value || !priceDistrict.value || !priceCrop.value || !priceArea.value) {
            return UI.showMessage('Please fill in all fields.', 'warning');
        }

        UI.setButtonLoading(findPriceBtn, true);
        priceResultsDisplay.innerHTML = UI.getLoaderHTML('Fetching Market Prices...');

        const payload = { 
            state: priceState.value,
            district: priceDistrict.value,
            crop: priceCrop.value,
            area: priceArea.value,
            lang: getCurrentLanguage()
        };

        try {
            const data = await API.getMandiPrices(payload);
            const priceHtml = ReportFormatter.displayPriceInfo(data.result);
            UI.animateContentSwap(priceResultsDisplay, priceHtml);
        } catch (error) {
            UI.showMessage(error.message, 'error');
            priceResultsDisplay.innerHTML = `<p class="text-red-600 text-center">${error.message}</p>`;
        } finally {
            UI.setButtonLoading(findPriceBtn, false);
        }
    }

    async function fetchAndRenderReports() {
        if (!elements.myReportsContent) return;
        elements.myReportsContent.innerHTML = UI.getLoaderHTML('Loading Your Reports...');
        try {
            const data = await API.fetchReports();
            const renderFunction = (container) => {
            ReportFormatter.renderMyReports(data.reports, container, {
                viewReportCallback: (reportData) => {
                    UI.showSection('analyzeFieldSection');
                    const reportHtml = ReportFormatter.displayFieldReport(reportData, reportData.lang || 'en');
                    UI.animateContentSwap(elements.fieldResultsDisplay, reportHtml);
                    elements.saveReportBtn.style.display = 'none';
                },
                deleteReportCallback: async (reportId) => {
                    try {
                        const response = await API.deleteReport(reportId);
                        UI.showMessage(response.message, 'success');
                        fetchAndRenderReports();
                    } catch (error) { UI.showMessage(error.message, 'error'); }
                }
            });
        };
        UI.animateContentSwap(elements.myReportsContent, renderFunction);
        } catch (error) { elements.myReportsContent.innerHTML = `<p class="text-red-600 text-center">${error.message}</p>`; }
    }

    // REPLACE the old function in script.js with this new one

    async function populateFertilizerReportDropdown() {
        const select = elements.fertilizerReportSelect;
        if (!select) return;
        select.innerHTML = '<option value="">-- Loading reports... --</option>';
        select.disabled = true;

        try {
            const data = await API.fetchReports();
            if (data.reports && data.reports.length > 0) {
                select.innerHTML = '<option value="">-- Select a report --</option>';
                data.reports.forEach(report => {
                    // --- THIS IS THE CORRECTED FIX ---
                    let reportData = report.report_data;
                    if (typeof reportData === 'string') {
                        // If the data is a string, parse it.
                        reportData = JSON.parse(reportData);
                    }
                    // If it's already an object, do nothing.
                    
                    const reportDate = new Date(reportData.generated_at).toLocaleDateString();
                    const topCrop = reportData.recommendations?.recommended_crops?.[0] || 'N/A';
                    const option = new Option(`Report from ${reportDate} (Crop: ${topCrop})`, report.id);
                    select.appendChild(option);
                });
                select.disabled = false;
            } else {
                select.innerHTML = '<option value="">-- No saved reports found --</option>';
            }
        } catch (error) {
            console.error("Error populating fertilizer dropdown:", error);
            UI.showMessage('Could not load your reports.', 'error');
            select.innerHTML = '<option value="">-- Error loading reports --</option>';
        }
    }
    
    async function handleGetFertilizerPlan() {
        if (!elements.fertilizerReportSelect || !elements.getFertilizerPlanBtn || !elements.fertilizerResultsDisplay) return;
        const reportId = elements.fertilizerReportSelect.value;
        if (!reportId) {
            return UI.showMessage('Please select a report first.', 'warning');
        }

        UI.setButtonLoading(elements.getFertilizerPlanBtn, true);
        elements.fertilizerResultsDisplay.innerHTML = UI.getLoaderHTML('Generating your plan...');

        try {
            const data = await API.getFertilizerPlan(reportId);
            if (data.success && data.plan) {
                const planHtml = ReportFormatter.displayFertilizerPlan(data.plan);
                UI.animateContentSwap(elements.fertilizerResultsDisplay, planHtml);
            } else {
                throw new Error(data.error || 'Could not generate a plan for this report.');
            }
        } catch (error) {
            UI.showMessage(error.message, 'error');
            elements.fertilizerResultsDisplay.innerHTML = `<p class="text-red-600 text-center">${error.message}</p>`;
        } finally {
            UI.setButtonLoading(elements.getFertilizerPlanBtn, false);
        }
    }
    
    function getGeolocation() {
        if (!navigator.geolocation || !elements.getLocationBtn) return UI.showMessage('Geolocation is not supported.', 'warning');
        UI.setButtonLoading(elements.getLocationBtn, true);
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                elements.latitude.value = pos.coords.latitude.toFixed(6);
                elements.longitude.value = pos.coords.longitude.toFixed(6);
                UI.setButtonLoading(elements.getLocationBtn, false);
            },
            (err) => {
                UI.showMessage(`Error: ${err.message}.`, 'error');
                UI.setButtonLoading(elements.getLocationBtn, false);
            }
        );
    }
    
    async function initializeLocationDropdowns() {
        try {
            locationData = await API.getLocations();
            const stateDropdown = elements.priceState;
            if (!stateDropdown) return;
            stateDropdown.innerHTML = '<option value="">-- Select State --</option>';
            for (const state of Object.keys(locationData).sort()) {
                stateDropdown.appendChild(new Option(state, state));
            }
        } catch (error) { UI.showMessage("Could not load location data.", "error"); }
    }

    function updateDistrictDropdown() {
        const { priceState, priceDistrict } = elements;
        if (!priceState || !priceDistrict) return;
        const selectedState = priceState.value;
        priceDistrict.innerHTML = '';
        if (selectedState && locationData) {
            priceDistrict.disabled = false;
            priceDistrict.innerHTML = '<option value="">-- Select District --</option>';
            locationData[selectedState].forEach(district => priceDistrict.appendChild(new Option(district, district)));
        } else {
            priceDistrict.disabled = true;
            priceDistrict.innerHTML = '<option value="">-- Select State First --</option>';
        }
    }

    function attachAuthEventListeners() {
        if (elements.loginForm) elements.loginForm.addEventListener('submit', handleLogin);
        if (elements.registerForm) elements.registerForm.addEventListener('submit', handleRegister);
        if (elements.showRegister) elements.showRegister.addEventListener('click', (e) => { e.preventDefault(); UI.toggleAuthForms(false); });
        if (elements.showLogin) elements.showLogin.addEventListener('click', (e) => { e.preventDefault(); UI.toggleAuthForms(true); });
    }

    function attachMainAppEventListeners() {
        elements.navLinks.forEach(link => link.addEventListener('click', (e) => {
            e.preventDefault();
            const target = e.currentTarget.dataset.page;
            UI.showSection(target);
            if (target === 'myReportsSection') fetchAndRenderReports();
            if (target === 'dashboardSection') loadDashboardData();
            if (target === 'fertilizerInfoSection') populateFertilizerReportDropdown();
        }));
        if (elements.dashboardCtaBtn) elements.dashboardCtaBtn.addEventListener('click', () => UI.showSection('analyzeFieldSection'));
        if (elements.logoutBtn) elements.logoutBtn.addEventListener('click', handleLogout);
        if (elements.analyzeCropBtn) elements.analyzeCropBtn.addEventListener('click', handleAnalyzeCrop);
        if (elements.analyzeFieldBtn) elements.analyzeFieldBtn.addEventListener('click', handleAnalyzeField);
        if (elements.saveReportBtn) elements.saveReportBtn.addEventListener('click', handleSaveReport);
        if (elements.getLocationBtn) elements.getLocationBtn.addEventListener('click', getGeolocation);
        if (elements.priceState) elements.priceState.addEventListener('change', updateDistrictDropdown);
        if (elements.findPriceBtn) elements.findPriceBtn.addEventListener('click', handleGetMandiPrices);
        if (elements.cropImageUpload) elements.cropImageUpload.addEventListener('change', () => UI.displayImagePreview(elements.cropImageUpload, elements.cropImagePreview));
        if (elements.soilImageUpload) elements.soilImageUpload.addEventListener('change', () => UI.displayImagePreview(elements.soilImageUpload, elements.soilImagePreview));
        if (elements.changePasswordForm) elements.changePasswordForm.addEventListener('submit', handleChangePassword);
        if (elements.deleteAccountBtn) elements.deleteAccountBtn.addEventListener('click', handleDeleteAccount);
        if (elements.getFertilizerPlanBtn) elements.getFertilizerPlanBtn.addEventListener('click', handleGetFertilizerPlan);
    }
    
    // --- DRISHTI CHATBOT LOGIC ---
    const chatToggleBtn = document.getElementById('drishti-chat-toggle');
    const chatCloseBtn = document.getElementById('drishti-chat-close');
    const chatWindow = document.getElementById('drishti-chat-window');
    const chatForm = document.getElementById('drishti-chat-form');
    const chatInput = document.getElementById('drishti-chat-input');
    const messageArea = document.getElementById('drishti-message-area');
    const typingIndicator = document.getElementById('drishti-typing-indicator');
    const ctaBubble = document.getElementById('drishti-cta-bubble');
    const ctaCloseBtn = document.getElementById('drishti-cta-close');

    let drishtiChatHistory = [];
    let isChatInitialized = false;

    const hideCtaBubble = () => { if (ctaBubble) ctaBubble.classList.remove('active'); };

    setTimeout(() => { if (ctaBubble) ctaBubble.classList.add('active'); }, 3000);
    setTimeout(hideCtaBubble, 15000);
    if (ctaCloseBtn) ctaCloseBtn.addEventListener('click', hideCtaBubble);

    const addMessageToChat = (text, isUser) => {
        const messageRow = document.createElement('div');
        messageRow.className = `chat-message-row ${isUser ? 'user' : 'bot'}`;

        const avatarInitial = isUser ? (elements.navbarUsername.textContent ? elements.navbarUsername.textContent[0].toUpperCase() : 'U') : '';
        const avatarClass = isUser ? 'user' : 'bot';
        const contentClass = isUser ? 'user' : 'bot';
        
        const botAvatarHTML = `
            <div class="chat-avatar bot !bg-transparent">
                <img src="/static/images/logo.png" alt="Drishti" class="w-full h-full object-cover rounded-full">
            </div>`;
        
        messageRow.innerHTML = `
            ${!isUser ? botAvatarHTML : ''}
            <div class="message-content ${contentClass}">
                <p>${text.replace(/\n/g, '<br>')}</p>
                <div class="chat-timestamp">${getCurrentTime()}</div>
            </div>
            ${isUser ? `<div class="chat-avatar ${avatarClass}">${avatarInitial}</div>` : ''}
        `;
        messageArea.appendChild(messageRow);
        messageArea.scrollTop = messageArea.scrollHeight;
    };

    const addDrishtiResponse = (response) => {
        const messageRow = document.createElement('div');
        messageRow.className = 'chat-message-row bot';

        let formattedContent = '';

        if (typeof response.content === 'string') {
            formattedContent = response.content.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        } else if (Array.isArray(response.content)) {
            formattedContent = response.content.map(item => {
                const title = item.title ? `<strong>${item.title}</strong><br>` : '';
                const description = item.description || '';
                return `${title}${description.replace(/\n/g, '<br>')}`;
            }).join('<br><br>'); 
        } else {
            formattedContent = 'Received complex data. Please check the console.';
            console.log('Received unexpected response content:', response.content);
        }

        messageRow.innerHTML = `
            <div class="chat-avatar bot !bg-transparent">
                <img src="/static/images/logo.png" alt="Drishti" class="w-full h-full object-cover rounded-full">
            </div>
            <div class="message-content bot">
                <p>${response.content.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</p>
                <div class="chat-timestamp">${getCurrentTime()}</div>
            </div>
        `;
        messageArea.appendChild(messageRow);

        if (response.type === 'options' && response.options?.length > 0) {
            const optionsContainer = document.createElement('div');
            // Corrected padding to align with the message bubble, not the avatar
            optionsContainer.className = 'chat-options-container pl-16'; 
            response.options.forEach(option => {
                const button = document.createElement('button');
                button.className = 'chat-option-btn';
                button.textContent = option.label;
                button.dataset.payload = JSON.stringify(option.payload);
                optionsContainer.appendChild(button);
            });
            messageArea.appendChild(optionsContainer);
        }
        messageArea.scrollTop = messageArea.scrollHeight;
    };

    const sendToDrishti = async (payload) => {
        typingIndicator.style.display = 'block';
        chatInput.disabled = true;
        document.querySelectorAll('.chat-option-btn').forEach(btn => btn.disabled = true);
        
        try {
            const data = await API.chatWithDrishti(payload);
            addDrishtiResponse(data.reply);
            drishtiChatHistory = data.history || [];
        } catch (error) {
            addDrishtiResponse({ type: 'text', content: `Sorry, an error occurred: ${error.message}` });
        } finally {
            typingIndicator.style.display = 'none';
            chatInput.disabled = false;
            chatInput.focus();
        }
    };
    
    const initializeChat = () => {
        if (isChatInitialized) return;
        messageArea.innerHTML = ''; // Clear any default messages
        isChatInitialized = true;
        sendToDrishti({ event: 'init_chat' });
    };

    if (chatToggleBtn) {
        chatToggleBtn.addEventListener('click', () => {
            hideCtaBubble();
            chatWindow.classList.toggle('active');
            if (chatWindow.classList.contains('active')) initializeChat();
        });
    }

    if (chatCloseBtn) chatCloseBtn.addEventListener('click', () => chatWindow.classList.remove('active'));

    if (chatForm) {
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const userMessage = chatInput.value.trim();
            if (!userMessage) return;
            addMessageToChat(userMessage, true);
            chatInput.value = '';
            sendToDrishti({ message: userMessage, history: drishtiChatHistory });
        });
    }

    if (messageArea) {
        messageArea.addEventListener('click', (e) => {
            if (e.target.classList.contains('chat-option-btn')) {
                const button = e.target;
                const payload = JSON.parse(button.dataset.payload);
                addMessageToChat(button.textContent, true);
                if (button.parentElement) button.parentElement.remove();
                sendToDrishti({ message: payload.message, history: drishtiChatHistory });
            }
        });
    }
    
    checkAuthenticationAndInit();
});