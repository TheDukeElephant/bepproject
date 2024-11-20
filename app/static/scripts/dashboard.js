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
        const { co2, temperature, humidity } = data;
        const now = new Date().toLocaleTimeString();

        // Update CO₂ chart
        co2Chart.data.labels.push(now);
        co2Chart.data.datasets[0].data.push(co2);
        if (co2Chart.data.labels.length > 10) {
            co2Chart.data.labels.shift();
            co2Chart.data.datasets[0].data.shift();
        }
        co2Chart.update();

        // Update Temperature chart
        tempChart.data.labels.push(now);
        tempChart.data.datasets[0].data.push(temperature);
        if (tempChart.data.labels.length > 10) {
            tempChart.data.labels.shift();
            tempChart.data.datasets[0].data.shift();
        }
        tempChart.update();

        // Update Humidity chart
        humidityChart.data.labels.push(now);
        humidityChart.data.datasets[0].data.push(humidity);
        if (humidityChart.data.labels.length > 10) {
            humidityChart.data.labels.shift();
            humidityChart.data.datasets[0].data.shift();
        }
        humidityChart.update();
    });
});
