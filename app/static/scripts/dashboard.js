document.addEventListener("DOMContentLoaded", () => {
    const socket = io({
        reconnection: true,
        reconnectionAttempts: 5, // Try 5 times before giving up
        reconnectionDelay: 1000 // Wait 1 second between attempts
    });

    let lastTimestamp = 0; // Track the most recent update timestamp
    const co2Values = []; // Array to hold the last 10 CO2 values

    // Set up chart data for CO₂
    const co2Chart = new Chart(document.getElementById('co2Chart').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'CO₂ (%)',
                data: [],
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
            }]
        },
        options: { 
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    suggestedMax: 0.1
                }
            }
        }
    });

    // Set up chart data for O₂
    const o2Chart = new Chart(document.getElementById('o2Chart').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'O₂ (ppm)',
                data: [],
                borderColor: 'rgba(80, 102, 192, 1)',
                backgroundColor: 'rgba(80, 102, 192, 0.2)',
            }]
        },
        options: { responsive: true }
    });

    // Set up chart data for Temperature
    const tempChart = new Chart(document.getElementById('tempChart').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Temperature 1 (°C)',
                    data: [],
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                },
                {
                    label: 'Temperature 2 (°C)',
                    data: [],
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                },
                {
                    label: 'Temperature 3 (°C)',
                    data: [],
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                },
                {
                    label: 'Temperature 4 (°C)',
                    data: [],
                    borderColor: 'rgba(153, 102, 255, 1)',
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                },
                {
                    label: 'Temperature 5 (°C)',
                    data: [],
                    borderColor: 'rgba(255, 159, 64, 1)',
                    backgroundColor: 'rgba(255, 159, 64, 0.2)',
                }
            ]
        },
        options: { 
            responsive: true,
            scales: {
                y: {
                    min: 13,
                    max: 21
                }
            }
        }
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

        const { co2, o2, temperatures, humidity } = data;

        const now = new Date().toLocaleTimeString();

        // Update CO₂ value and chart
        const co2Value = typeof co2 === 'number' ? co2 : 0.04; // Fallback to 400 ppm if invalid
        document.getElementById('co2').textContent = `${co2Value} %`;
        updateChart(co2Chart, now, co2Value);
        updateCO2YAxis(co2Value); // Update Y-axis based on the latest CO2 value

        // Update O₂ value and chart
        const o2Value = typeof o2 === 'number' ? o2 : 21; // Fallback to 21% if invalid
        document.getElementById('o2').textContent = `${o2Value} %`;
        updateChart(o2Chart, now, o2Value);

        // Update Temperature values and chart
        temperatures.forEach((temp, index) => {
            let tempDisplayValue;
            if (typeof temp === 'number' && temp <= 950) {
                tempDisplayValue = `${temp} °C`;
                updateChart(tempChart, now, temp, index);
            } else {
                tempDisplayValue = 'Not connected';
            }
            document.getElementById(`temp${index + 1}`).textContent = tempDisplayValue;
        });

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
     * @param {number} [datasetIndex=0] - The index of the dataset to update.
     */
    function updateChart(chart, label, value, datasetIndex = 0) {
        if (chart.data.labels.length === 0 || chart.data.labels[chart.data.labels.length - 1] !== label) {
            chart.data.labels.push(label);
        }
        chart.data.datasets[datasetIndex].data.push(value);

        if (chart.data.datasets[datasetIndex].data.length > 10) {
            chart.data.datasets[datasetIndex].data.shift();
        }

        if (chart.data.labels.length > 10) {
            chart.data.labels.shift();
        }

        // Dynamically adjust y-axis range only for the temperature chart
        if (chart === tempChart) {
            const minTemp = Math.min(...chart.data.datasets.flatMap(dataset => dataset.data));
            const maxTemp = Math.max(...chart.data.datasets.flatMap(dataset => dataset.data));
            chart.options.scales.y.min = Math.min(13, minTemp);
            chart.options.scales.y.max = Math.max(21, maxTemp);
        }

        chart.update();
    }

    /**
     * Updates the Y-axis of the CO2 chart based on the maximum CO2 value in the last 10 readings.
     * If the maximum value exceeds 1000, adjust the Y-axis to go from 0 to max_value + 100.
     * @param {number} co2Value - The current CO2 reading.
     */
    function updateCO2YAxis(co2Value) {
        co2Values.push(co2Value);

        // Keep only the last 10 CO2 values
        if (co2Values.length > 10) {
            co2Values.shift();
        }

        // Find the max value in the last 10 CO2 readings
        const maxCO2 = Math.max(...co2Values);

        // Set Y-axis range based on the max value
        const newMax = maxCO2 > 0.1 ? maxCO2 + 0.05 : 0.1;

        // Update the Y-axis of the CO2 chart
        co2Chart.options.scales.y.suggestedMax = newMax;
        co2Chart.update();
    }
});
