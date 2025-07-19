import { getCurrentLanguage } from './i18n.js'; 

const reportTranslations = {
    en: {
        report_title: "Field Analysis Report",
        generated: "Generated",
        location_weather: "Location & Current Weather",
        state: "State",
        current_weather: "Current Weather",
        climate_summary: "Annual Climate Summary",
        soil_analysis: "Soil Analysis",
        soil_type: "Detected Soil Type",
        confidence: "Confidence",
        recommendations: "Crop Recommendations",
        ai_plan: "General AI Action Plan",
        kharif: "Kharif (Monsoon)",
        rabi: "Rabi (Winter)",
        avg_temp: "Avg Temp",
        total_rain: "Total Rain"
    },
    hi: {
        report_title: "खेत विश्लेषण रिपोर्ट",
        generated: "उत्पन्न",
        location_weather: "स्थान और वर्तमान मौसम",
        state: "राज्य",
        current_weather: "वर्तमान मौसम",
        climate_summary: "वार्षिक जलवायु सारांश",
        soil_analysis: "मिट्टी का विश्लेषण",
        soil_type: "पता लगाया गया मिट्टी का प्रकार",
        confidence: "आत्मविश्वास",
        recommendations: "फसल की सिफारिशें",
        ai_plan: "सामान्य एआई कार्य योजना",
        kharif: "खरीफ (मानसून)",
        rabi: "रबी (सर्दी)",
        avg_temp: "औसत तापमान",
        total_rain: "कुल वर्षा"
    }
};

function formatNumber(value, fixed = 1) {
    const num = parseFloat(value);
    return !isNaN(num) ? num.toFixed(fixed) : 'N/A';
}

function createListItem(label, value, unit = '') {
    if (value === undefined || value === null || value === 'N/A' || value === '' || Number.isNaN(value)) return '';
    return `<p><strong class="font-medium text-gray-800">${label}:</strong> ${value}${unit}</p>`;
}

function formatDate_DDMMYYYY(dateString) {
    if (!dateString) return 'Invalid Date';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
        return 'Invalid Date';
    }
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}-${month}-${year}`;
}

export function displayCropAnalysis(resultData) {
    if (!resultData) return '';

    const { prediction, confidence, is_healthy, detailed_advice } = resultData;
    const confidencePercent = formatNumber(confidence * 100, 1);
    
    const healthStatusHtml = is_healthy 
        ? `<p class="text-2xl font-bold text-green-600 mb-2">Healthy</p>`
        : `<p class="text-2xl font-bold text-red-600 mb-2">Potential Issue Detected</p>`;

    // --- [THIS IS THE CORRECTED FUNCTION] ---
    const formatAiAdvice = (advice) => {
        // Handle cases where advice is missing or not an array
        if (!Array.isArray(advice) || advice.length === 0) {
            // If advice is an object (likely an error message), display it
            if (advice && typeof advice === 'object' && !Array.isArray(advice)) {
                return `<p>${advice.title || 'Error'}: ${advice.description || 'No detailed advice available.'}</p>`;
            }
            return "<p>No detailed advice available.</p>";
        }

        // Define icons for different sections to add visual cues
        const icons = {
            'Description': `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`,
            'Symptoms': `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>`,
            'Treatment': `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`,
            'Prevention': `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>`,
        };

        // Loop through the array of advice objects and build the HTML
        return advice.map(item => {
            const title = item.title || 'Advice';
            const description = item.description || 'No details available.';
            const icon = icons[title] || icons['Description'];

            return `
                <div class="mb-6 bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <h4 class="font-bold text-lg text-gray-800 flex items-center gap-3 mb-3">
                        <span class="text-emerald-600">${icon}</span>
                        ${title}
                    </h4>
                    <p class="text-gray-700 pl-9">${description.replace(/\n/g, '<br>')}</p>
                </div>
            `;
        }).join('');
    };
    
    const resultHtml = `
        <div class="text-left p-2 md:p-4 w-full">
            <div class="text-center mb-6">
                ${healthStatusHtml}
                <p class="text-xl text-gray-800 font-semibold">${prediction}</p>
                <p class="text-md text-gray-500">Model Confidence: ${confidencePercent}%</p>
            </div>
            <hr class="my-6">
            <div>
                <h3 class="font-semibold text-2xl text-gray-800 mb-4">AI-Powered Detailed Analysis:</h3>
                <div class="space-y-4">${formatAiAdvice(detailed_advice)}</div>
            </div>
        </div>`;
    return resultHtml;
}

export function displayFieldReport(reportData, lang) {
    if (!reportData) return;

    const currentLang = lang || 'en';
    const T = reportTranslations[currentLang];

    if (!T) {
        console.error("Invalid language provided to report formatter:", currentLang);
        return; 
    }

    const { location, weather, historical_weather, soil_analysis, recommendations, ai_advice, generated_at } = reportData;
    const recommendationsHtml = recommendations?.recommended_crops?.join(', ') || 'No recommendations available.';
    
    const soilHtml = soil_analysis.note
        ? `<p class="text-gray-500">${soil_analysis.note}</p>`
        : `<p><strong class="font-medium">${T.soil_type}:</strong> ${soil_analysis.prediction} (${T.confidence}: ${formatNumber(soil_analysis.confidence * 100, 1)}%)</p>`;
    
    const formatAiAdvice = (advice) => {
        if (!Array.isArray(advice) || advice.length === 0) {
            return '<p>No AI advice available.</p>';
        }
        return advice.map(item => `
            <div class="bg-purple-50 border border-purple-200 p-4 rounded-lg">
                <div class="flex items-center">
                    <div class="bg-purple-200 text-purple-700 rounded-full p-2 mr-3">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    </div>
                    <h4 class="font-semibold text-lg text-purple-800">${item.title}</h4>
                </div>
                <p class="text-purple-700 mt-2 pl-12 text-sm">${item.description}</p>
            </div>
        `).join('');
    };

    const historicalWeatherHtml = `
        <div class="p-3 bg-cyan-50 rounded-lg">
            <h4 class="font-semibold text-lg text-cyan-700">${T.climate_summary}</h4>
            <div class="grid grid-cols-2 gap-x-4 text-sm mt-2">
                <div>
                    <p class="font-semibold">${T.kharif}</p>
                    ${createListItem(T.avg_temp, formatNumber(historical_weather?.kharif_avg_temp, 0), '°C')}
                    ${createListItem(T.total_rain, formatNumber(historical_weather?.kharif_total_rainfall, 0), ' mm')}
                </div>
                <div>
                    <p class="font-semibold">${T.rabi}</p>
                    ${createListItem(T.avg_temp, formatNumber(historical_weather?.rabi_avg_temp, 0), '°C')}
                    ${createListItem(T.total_rain, formatNumber(historical_weather?.rabi_total_rainfall, 0), ' mm')}
                </div>
            </div>
            ${historical_weather?.note ? `<p class="text-xs text-orange-600 mt-2 p-2 bg-orange-100 rounded-md">${historical_weather.note}</p>` : ''}
        </div>`;
    
    const reportHtml = `
        <h3 class="text-2xl font-bold text-emerald-800 mb-2">${T.report_title}</h3>
        <p class="text-xs text-gray-400 mb-4">${T.generated}: ${formatDate_DDMMYYYY(generated_at)}</p>
        <div class="space-y-5">
            <div class="p-3 bg-gray-50 rounded-lg"><h4 class="font-semibold text-lg text-gray-700">${T.location_weather}</h4>${createListItem(T.state, location.state)}${createListItem(T.current_weather, `${formatNumber(weather?.temperature, 0)}°C, ${weather?.description}`)}</div>
            ${historicalWeatherHtml}
            <div class="p-3 bg-gray-50 rounded-lg"><h4 class="font-semibold text-lg text-gray-700">${T.soil_analysis}</h4>${soilHtml}</div>
            <div class="p-3 bg-green-50 rounded-lg"><h4 class="font-semibold text-lg text-green-700">${T.recommendations}</h4><p class="font-medium">${recommendationsHtml}</p><p class="text-sm text-gray-600 mt-1">${recommendations?.considerations || ''}</p></div>
            <div>
                <h4 class="font-semibold text-lg text-gray-700 mb-2">${T.ai_plan}</h4>
                <div class="space-y-3">
                    ${formatAiAdvice(reportData.ai_advice)}
                </div>
            </div>
        </div>`;
    
    return reportHtml;
}

export function displayPriceInfo(resultData) {
    if (!resultData) return;
    const { crop, location, average_mandi_price, estimated_yield_qpa, total_estimated_revenue, area_acres, note, is_stale, stale_date } = resultData;
    
    const formatCurrency = (value) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value);
    const staleNoteHtml = is_stale 
        ? `<p class="text-xs text-orange-600 bg-orange-100 p-2 rounded-md my-2">Note: Live market data is currently unavailable. This price is from ${stale_date}.</p>` 
        : `<p class="text-xs text-green-700">${note || 'Based on recent prices in your district.'}</p>`;

    const resultHtml = `
        <div class="text-left p-4 w-full">
            <h3 class="text-2xl font-bold text-emerald-800 mb-4">Revenue Estimate</h3>
            <div class="space-y-3">
                <p><strong>Crop:</strong> ${crop}</p>
                <p><strong>Location:</strong> ${location}</p>
                <p><strong>Field Area:</strong> ${area_acres} acres</p>
                <hr class="my-2">
                
                <p><strong>Avg. Mandi Price:</strong> ₹ ${average_mandi_price || 'N/A'} / Quintal</p>
                
                ${staleNoteHtml}
                <p><strong>Estimated Yield:</strong> ~${estimated_yield_qpa} Quintals / Acre</p>
                <hr class="my-2">
                <div class="bg-green-100 p-4 rounded-lg text-center">
                    <p class="text-lg font-semibold text-green-800">Total Estimated Revenue</p>
                    <p class="text-3xl font-bold text-green-700">${formatCurrency(total_estimated_revenue)}</p>
                </div>
                <p class="text-xs text-center text-gray-500 mt-2">*This is an estimate. Actual revenue depends on final yield, quality, and real-time market conditions.</p>
            </div>
        </div>`;
    return resultHtml;
}

export function renderMyReports(reports, myReportsContentElement, callbacks) {
    if (!myReportsContentElement) return;
    if (!reports || reports.length === 0) {
        myReportsContentElement.innerHTML = `<p class="text-gray-600">You haven't saved any field reports yet.</p>`;
        return;
    }
    myReportsContentElement.innerHTML = `
        <ul class="space-y-3">
            ${reports.map(report => {
                const parsedData = typeof report.report_data === 'string' ? JSON.parse(report.report_data) : report.report_data;
                const reportDate = formatDate_DDMMYYYY(parsedData?.generated_at);
                return `
                <li class="bg-white p-4 rounded-lg shadow-sm border flex justify-between items-center">
                    <div>
                        <p class="font-semibold text-gray-700">Report from ${reportDate}</p>
                        <p class="text-sm text-gray-500">Location: Lat ${formatNumber(report.latitude, 2)}, Lon ${formatNumber(report.longitude, 2)}</p>
                    </div>
                    <div class="flex space-x-2">
                        <button class="view-report-btn text-sm bg-blue-100 text-blue-700 px-3 py-1 rounded hover:bg-blue-200" data-report-id="${report.id}">View</button>
                        <button class="delete-report-btn text-sm bg-red-100 text-red-700 px-3 py-1 rounded hover:bg-red-200" data-report-id="${report.id}">Delete</button>
                    </div>
                </li>`;
            }).join('')}
        </ul>`;

    myReportsContentElement.querySelectorAll('.view-report-btn').forEach(button => {
        button.addEventListener('click', () => {
            const report = reports.find(r => r.id == button.dataset.reportId);
            if (report && report.report_data) {
                 const reportData = typeof report.report_data === 'string' ? JSON.parse(report.report_data) : report.report_data;
                 callbacks.viewReportCallback(reportData);
            }
        });
    });

    myReportsContentElement.querySelectorAll('.delete-report-btn').forEach(button => {
        button.addEventListener('click', () => {
            callbacks.deleteReportCallback(button.dataset.reportId);
        });
    });
}

export function displayFertilizerPlan(plan) {
    if (!plan) { 
        return `<p class="text-center text-gray-500">Could not generate a plan.</p>`;
    }
    
    const formatStructuredAdvice = (adviceList) => {
        if (!Array.isArray(adviceList) || adviceList.length === 0) {
            return "<p>No detailed advice available.</p>";
        }

        return adviceList.map(item => {
            const descriptionHtml = item.description
                .replace(/\* (.*?)(?=\* |$)/g, '<li class="flex items-start"><span class="mr-2 mt-1 text-teal-600">▪</span><span>$1</span></li>')
                .replace(/(\r\n|\n|\r)/g, "");

            return `
                <div class="mt-4">
                    <h5 class="font-semibold text-teal-800 text-md flex items-center">
                         <span class="mr-2">🌱</span> ${item.title}
                    </h5>
                    <ul class="text-sm text-teal-900 mt-1 pl-6 space-y-1">
                        ${descriptionHtml}
                    </ul>
                </div>
            `;
        }).join('');
    };

    const adviceHtml = Array.isArray(plan.ai_application_advice)
        ? formatStructuredAdvice(plan.ai_application_advice)
        : `<div class="text-sm text-teal-900 whitespace-pre-wrap mt-2">${plan.ai_application_advice}</div>`;

    const planHtml = `
        <div class="text-left w-full">
            <h3 class="text-2xl font-bold text-emerald-800 mb-4">Fertilizer Plan for ${plan.crop}</h3>
            <div class="p-4 bg-teal-50 rounded-lg border border-teal-200">
                <p class="text-sm text-gray-600 mb-2">Approximate nutrients to add per acre:</p>
                <div class="grid grid-cols-3 gap-2 text-center mb-4">
                    <div class="bg-white p-3 rounded-lg shadow-sm">
                        <strong class="block text-gray-800">Nitrogen (N)</strong>
                        <span class="text-xl font-bold">${plan.n_needed} kg</span>
                    </div>
                    <div class="bg-white p-3 rounded-lg shadow-sm">
                        <strong class="block text-gray-800">Phosphorus (P)</strong>
                        <span class="text-xl font-bold">${plan.p_needed} kg</span>
                    </div>
                    <div class="bg-white p-3 rounded-lg shadow-sm">
                        <strong class="block text-gray-800">Potassium (K)</strong>
                        <span class="text-xl font-bold">${plan.k_needed} kg</span>
                    </div>
                </div>
                <h4 class="font-semibold text-md text-gray-800 mt-4">AI Application Advice:</h4>
                ${adviceHtml}
            </div>
            <p class="text-xs text-gray-500 mt-3">*This is a general recommendation based on average soil data for your state. For best results, conduct a detailed soil test.</p>
        </div>
    `;
    return planHtml;
}