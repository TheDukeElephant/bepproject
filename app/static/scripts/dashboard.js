document.addEventListener("DOMContentLoaded", () => {
    const socket = io({
        reconnection: true,
        reconnectionAttempts: 5, // Try 5 times before giving up
        reconnectionDelay: 1000 // Wait 1 second between attempts
    });

    let lastTimestamp = 0; // Track the most recent update timestamp

    // Set up chart data for CO₂
    const co2Chart = new Chart(document.getElementById('co2Chart').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'CO₂ (ppm)',
                data: [],
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
            }]
        },
        options: { responsive: true }
    });

    // Set up chart data for O₂
    const o2Chart = new Chart(document.getElementById('o2Chart').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'O₂ (ppm)',
                data: [],
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
            }]
        },
        options: { responsive: true }
    });

    // Set up chart data for Temperature
    const tempChart = new Chart(document.getElementById('tempChart').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Temperature (°C)',
                data: [],
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
            }]
        },
        options: { responsive: true }
    });

    // Set up chart data for Humidity
    const humidityChart = new Chart(document.getElementById('humidityChart').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Humidity (%)',
                data: [],
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
            }]
        },
        options: { responsive: true }
    });

    // Listen for dashboard updates
    socket.on('update_dashboard', (data, callback) => {
        console.log('Received data:', data);

        // Validate timestamps to ensure we don't process stale data
        if (data.timestamp <= lastTimestamp) {
            console.warn('Stale data received, ignoring:', data);
            if (callback) callback('Stale data ignored.');
            return;
        }
        lastTimestamp = data.timestamp;

        const { co2, o2, temperature, humidity } = data;

        const now = new Date().toLocaleTimeString();

        // Update CO₂ value and chart
        const co2Value = typeof co2 === 'number' ? co2 : 400; // Fallback to 400 ppm if invalid
        document.getElementById('co2').textContent = `${co2Value} ppm`;
        updateChart(co2Chart, now, co2Value);

        // Update O₂ value and chart
        const o2Value = typeof o2 === 'number' ? o2 : 21; // Fallback to 21% if invalid
        document.getElementById('o2').textContent = `${o2Value} ppm`;
        updateChart(o2Chart, now, o2Value);

        // Update Temperature value and chart
        const tempValue = typeof temperature === 'number' ? temperature : 22.0; // Fallback to 22°C if invalid
        document.getElementById('temperature').textContent = `${tempValue} °C`;
        updateChart(tempChart, now, tempValue);

        // Update Humidity value and chart
        const humidityValue = typeof humidity === 'number' ? humidity : 50.0; // Fallback to 50% if invalid
        document.getElementById('humidity').textContent = `${humidityValue} %`;
        updateChart(humidityChart, now, humidityValue);

        // Acknowledge update back to server
        if (callback) callback('Dashboard update received and processed.');
    });

    socket.on('connect', () => {
        console.log('Connected to server');
        socket.emit('request_data'); // Request buffered data after reconnecting
    });

    socket.on('disconnect', () => {
        console.warn('Disconnected from server. Attempting to reconnect...');
    });

    /**
     * Updates the given chart with new data.
     * @param {Chart} chart - The chart to update.
     * @param {string} label - The label for the new data point.
     * @param {number} value - The value for the new data point.
     */
    function updateChart(chart, label, value) {
        chart.data.labels.push(label);
        chart.data.datasets[0].data.push(value);
        if (chart.data.labels.length > 10) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }
        chart.update();
    }
});
