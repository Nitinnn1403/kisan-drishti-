// In frontend/api_client.js

// This is the public URL of your backend on Render.
const API_BASE_URL = 'https://kisandrishti.onrender.com';

async function handleResponse(response) {
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Server returned a non-JSON error response.' }));
        throw new Error(errorData.error || `Request failed with status ${response.status}`);
    }
    return response.json();
}

// --- ALL FUNCTIONS UPDATED TO USE BACKTICKS (`) ---

export async function loginUser(email, password) {
    const response = await fetch(`${API_BASE_URL}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    });
    return handleResponse(response);
}

export async function registerUser(username, contact, email, password) {
    const response = await fetch(`${API_BASE_URL}/api/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, contact, email, password }),
    });
    return handleResponse(response);
}

export async function logoutUser() {
    return handleResponse(await fetch(`${API_BASE_URL}/api/logout`, { method: 'POST' }));
}

export async function checkAuthStatus() {
    return handleResponse(await fetch(`${API_BASE_URL}/api/check_auth`));
}

export async function getDashboardSummary(lang) {
    return handleResponse(await fetch(`${API_BASE_URL}/api/dashboard_summary?lang=${lang}`));
}

export async function analyzeCrop(formData) {
    return handleResponse(await fetch(`${API_BASE_URL}/api/analyze_crop`, { method: 'POST', body: formData }));
}

export async function analyzeField(formData) {
    return handleResponse(await fetch(`${API_BASE_URL}/api/analyze_field`, { method: 'POST', body: formData }));
}

export async function getLocations() {
    return handleResponse(await fetch(`${API_BASE_URL}/api/locations`));
}

export async function getMandiPrices(payload) {
    const response = await fetch(`${API_BASE_URL}/api/mandi_prices`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    return handleResponse(response);
}

export async function saveReport(reportData) {
    const response = await fetch(`${API_BASE_URL}/api/save_report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report_data: reportData }),
    });
    return handleResponse(response);
}

export async function fetchReports() {
    return handleResponse(await fetch(`${API_BASE_URL}/api/reports`));
}

export async function deleteReport(reportId) {
    return handleResponse(await fetch(`${API_BASE_URL}/api/reports/${reportId}`, { method: 'DELETE' }));
}

export async function chatWithDrishti(payload) {
    const response = await fetch(`${API_BASE_URL}/api/chat_with_drishti`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    return handleResponse(response);
}

export async function changePassword(current_password, new_password) {
    const response = await fetch(`${API_BASE_URL}/api/change_password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_password, new_password }),
    });
    return handleResponse(response);
}

export async function deleteAccount() {
    return handleResponse(await fetch(`${API_BASE_URL}/api/delete_account`, { method: 'DELETE' }));
}

export async function getFertilizerPlan(reportId) {
    return handleResponse(await fetch(`${API_BASE_URL}/api/get_fertilizer_plan/${reportId}`));
}