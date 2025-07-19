// api_client.js - Final version with all API functions

async function handleResponse(response) {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Server returned a non-JSON error response.' }));
        throw new Error(errorData.error || `Request failed with status ${response.status}`);
    }
    return response.json();
}

// --- User Authentication ---

export async function loginUser(email, password) {
    const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }), // Use 'email' key
    });
    return handleResponse(response);
}

export async function registerUser(username, contact, email, password) { // Add new params
    const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // Send all new fields in the body
        body: JSON.stringify({ username, contact, email, password }),
    });
    return handleResponse(response);
}

export async function logoutUser() {
    return handleResponse(await fetch('/api/logout', { method: 'POST' }));
}

export async function checkAuthStatus() {
    return handleResponse(await fetch('/api/check_auth'));
}

export async function getDashboardSummary(lang) {
    return handleResponse(await fetch(`/api/dashboard_summary?lang=${lang}`));
}


// --- Analysis Features ---

export async function analyzeCrop(formData) {
    return handleResponse(await fetch('/api/analyze_crop', { method: 'POST', body: formData }));
}

export async function analyzeField(formData) {
    return handleResponse(await fetch('/api/analyze_field', { method: 'POST', body: formData }));
}


// --- Price Information Feature ---

export async function getLocations() {
    return handleResponse(await fetch('/api/locations'));
}

export async function getMandiPrices(payload) {
    const response = await fetch('/api/mandi_prices', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    return handleResponse(response);
}


// --- Report Management ---

export async function saveReport(reportData) {
    const response = await fetch('/api/save_report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report_data: reportData }),
    });
    return handleResponse(response);
}

export async function fetchReports() {
    return handleResponse(await fetch('/api/reports'));
}

export async function deleteReport(reportId) {
    return handleResponse(await fetch(`/api/reports/${reportId}`, { method: 'DELETE' }));
}

export async function chatWithDrishti(payload) { // Changed 'data' to 'payload'
    const response = await fetch('/api/chat_with_drishti', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload), // Send the entire payload object
    });
    return handleResponse(response);
}

export async function changePassword(current_password, new_password) {
    const response = await fetch('/api/change_password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_password, new_password }),
    });
    return handleResponse(response);
}

export async function deleteAccount() {
    return handleResponse(await fetch('/api/delete_account', { method: 'DELETE' }));
}

export async function getFertilizerPlan(reportId) {
    return handleResponse(await fetch(`/api/get_fertilizer_plan/${reportId}`));
}