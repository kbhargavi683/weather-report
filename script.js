// ============================================
// CONFIGURATION
// ============================================

let API_URL;

if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    // Local development
    API_URL = 'http://localhost:5000';
} else {
    
    API_URL = 'https://your-backend-url.onrender.com'; 
}

console.log('🌤️ API URL:', API_URL);

// ============================================
// DOM ELEMENTS
// ============================================
const cityInput = document.getElementById('cityInput');
const stateInput = document.getElementById('stateInput');
const searchBtn = document.getElementById('searchBtn');
const randomBtn = document.getElementById('randomBtn');
const resultDiv = document.getElementById('result');
const locationBtn = document.getElementById('locationBtn');
const notifBtn = document.getElementById('notifBtn');

const CITIES = [
    'Mumbai', 'Delhi', 'Hyderabad', 'Bangalore', 'Chennai',
    'Kolkata', 'Ahmedabad', 'Pune', 'Jaipur', 'Lucknow',
    'Nagpur', 'Indore', 'Moinabad', 'Warangal', 'Nizamabad',
    'Karimnagar', 'Khammam', 'Narayanpet', 'Mahabubnagar', 'Vikarabad'
];

// ============================================
// GET WEATHER
// ============================================
async function getWeather(city, state = '') {
    if (!city || city.trim() === '') {
        resultDiv.innerHTML = `
            <div class="error">
                <span class="icon">❌</span>
                Please enter a location
                <small>Example: Narayanpet, Telangana</small>
            </div>
        `;
        return;
    }

    const searchDisplay = state ? `${city}, ${state}` : city;
    resultDiv.innerHTML = `<div class="loading">⏳ Searching for ${searchDisplay}...</div>`;

    try {
        let url = `${API_URL}/weather?city=${encodeURIComponent(city.trim())}`;
        if (state && state.trim()) {
            url += `&state=${encodeURIComponent(state.trim())}`;
        }
        
        // Add cache-busting parameter
        url += `&t=${Date.now()}`;

        console.log('🌤️ Fetching:', url);

        const response = await fetch(url);
        const data = await response.json();

        console.log('📦 Response:', data);

        if (response.ok && data.city) {
            displayWeather(data);
            if (Notification.permission === 'granted') {
                sendNotification(data);
            }
        } else {
            // Improved error messages based on context
            let errorMsg = data.error || 'Location not found';
            let suggestion = '';
            
            // More helpful suggestions
            if (errorMsg.includes('not found')) {
                if (state) {
                    suggestion = `
                        <small>
                            💡 Try:
                            <br/>• Check state spelling (e.g., "Telangana", "Karnataka", "Maharashtra")
                            <br/>• Search without state
                            <br/>• Search for a nearby city in that state
                        </small>
                    `;
                } else {
                    suggestion = `
                        <small>
                            💡 Try:
                            <br/>• Add state: "${city}, Telangana"
                            <br/>• Add state: "${city}, Karnataka"
                            <br/>• Check spelling of location
                        </small>
                    `;
                }
            }
            
            resultDiv.innerHTML = `
                <div class="error">
                    <span class="icon">❌</span>
                    ${errorMsg}
                    ${suggestion}
                </div>
            `;
        }
    } catch (error) {
        console.error('❌ Error:', error);
        resultDiv.innerHTML = `
            <div class="error">
                <span class="icon">🔌</span>
                Backend server not running or not accessible
                <small>To use this app locally: cd backend && python app.py</small>
            </div>
        `;
    }
}

// ============================================
// DISPLAY WEATHER
// ============================================
function displayWeather(data) {
    resultDiv.innerHTML = `
        <div class="weather-card">
            <div class="weather-top">
                <div>
                    <div class="weather-city">${data.city}</div>
                    <div class="weather-region">${data.region || ''}</div>
                </div>
                <div class="weather-icon">${data.icon || '🌤️'}</div>
            </div>
            <div class="weather-temp">
                <span class="temp">${data.temperature}</span>
                <span class="unit">°C</span>
            </div>
            <div class="weather-desc">${data.description || 'Clear'}</div>
            <div class="weather-grid">
                <div class="item">
                    <div class="icon">💨</div>
                    <div class="label">Wind</div>
                    <div class="value">${data.wind}</div>
                </div>
                <div class="item">
                    <div class="icon">🧭</div>
                    <div class="label">Direction</div>
                    <div class="value">${data.direction}</div>
                </div>
                <div class="item">
                    <div class="icon">🕒</div>
                    <div class="label">Updated</div>
                    <div class="value">${data.time ? new Date(data.time).toLocaleTimeString() : 'Now'}</div>
                </div>
            </div>
        </div>
    `;
}

// ============================================
// NOTIFICATION
// ============================================
function sendNotification(data) {
    if (!('Notification' in window) || Notification.permission !== 'granted') return;
    try {
        new Notification('🌤️ Weather Update', {
            body: `${data.city}: ${data.temperature}°C, ${data.description}`,
            icon: '🌤️'
        });
    } catch (e) {}
}

// ============================================
// EVENT LISTENERS
// ============================================
searchBtn.addEventListener('click', () => {
    getWeather(cityInput.value.trim(), stateInput.value.trim());
});

cityInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') searchBtn.click();
});

stateInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') searchBtn.click();
});

randomBtn.addEventListener('click', () => {
    const city = CITIES[Math.floor(Math.random() * CITIES.length)];
    cityInput.value = city;
    stateInput.value = 'Telangana';
    getWeather(city, 'Telangana');
});

// ============================================
// LOCATION
// ============================================
locationBtn.addEventListener('click', () => {
    if (!navigator.geolocation) {
        resultDiv.innerHTML = `<div class="error"><span class="icon">❌</span>Geolocation not supported</div>`;
        return;
    }

    resultDiv.innerHTML = `<div class="loading">📍 Getting your location...</div>`;

    navigator.geolocation.getCurrentPosition(
        async (position) => {
            try {
                const { latitude, longitude } = position.coords;
                const response = await fetch(
                    `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json`
                );
                const data = await response.json();

                if (data && data.address) {
                    const city = data.address.city || data.address.town || data.address.village || 'Unknown';
                    const state = data.address.state || '';
                    cityInput.value = city;
                    stateInput.value = state;
                    getWeather(city, state);
                }
            } catch (error) {
                resultDiv.innerHTML = `<div class="error"><span class="icon">❌</span>Failed to get location</div>`;
            }
        },
        (error) => {
            let msg = 'Please allow location access';
            if (error.code === 1) msg = 'Location access denied';
            resultDiv.innerHTML = `<div class="error"><span class="icon">📍</span>${msg}</div>`;
        }
    );
});

// ============================================
// NOTIFICATIONS
// ============================================
notifBtn.addEventListener('click', () => {
    if (!('Notification' in window)) {
        alert('Notifications not supported');
        return;
    }

    if (Notification.permission === 'granted') {
        new Notification('🌤️ Weather Report', {
            body: 'Weather notifications enabled!',
            icon: '🌤️'
        });
        alert('✅ Notification sent!');
    } else {
        Notification.requestPermission().then(permission => {
            alert(permission === 'granted' ? '✅ Notifications enabled!' : '❌ Please allow notifications');
        });
    }
});

// ============================================
// START
// ============================================
console.log('🌤️ Weather App Started!');