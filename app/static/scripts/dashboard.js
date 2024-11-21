document.addEventListener("DOMContentLoaded", () => {
    const socket = io();

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
    socket.on('update_dashboard', (data) => {
        console.log('Received data:', data);
        const { co2, o2, temperature, humidity } = data;
    
        const now = new Date().toLocaleTimeString();
    
        // Update CO₂ value and chart
        const co2Value = typeof co2 === 'number' ? co2 : 400; // Fallback to 400 ppm if invalid
        document.getElementById('co2').textContent = `${co2Value} ppm`;
        co2Chart.data.labels.push(now);
        co2Chart.data.datasets[0].data.push(co2Value);
        if (co2Chart.data.labels.length > 10) {
            co2Chart.data.labels.shift();
            co2Chart.data.datasets[0].data.shift();
        }
        co2Chart.update();
    
        // Update O₂ value and chart
        const o2Value = typeof o2 === 'number' ? o2 : 21; // Fallback to 21% if invalid
        document.getElementById('o2').textContent = `${o2Value} ppm`;
        o2Chart.data.labels.push(now);
        o2Chart.data.datasets[0].data.push(o2Value);
        if (o2Chart.data.labels.length > 10) {
            o2Chart.data.labels.shift();
            o2Chart.data.datasets[0].data.shift();
        }
        o2Chart.update();
    
        // Update Temperature value and chart
        const tempValue = typeof temperature === 'number' ? temperature : 22.0; // Fallback to 22°C if invalid
        tempChart.data.labels.push(now);
        tempChart.data.datasets[0].data.push(tempValue);
        if (tempChart.data.labels.length > 10) {
            tempChart.data.labels.shift();
            tempChart.data.datasets[0].data.shift();
        }
        tempChart.update();
    
        // Update Humidity value and chart
        const humidityValue = typeof humidity === 'number' ? humidity : 50.0; // Fallback to 50% if invalid
        humidityChart.data.labels.push(now);
        humidityChart.data.datasets[0].data.push(humidityValue);
        if (humidityChart.data.labels.length > 10) {
            humidityChart.data.labels.shift();
            humidityChart.data.datasets[0].data.shift();
        }
        humidityChart.update();
    });
    
});
