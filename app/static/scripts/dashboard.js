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
        console.log('Received data:', data);
        const { co2, temperature, humidity } = data;
        if (typeof co2 !== 'number' || typeof temperature !== 'number' || typeof humidity !== 'number') {
            console.error('Invalid data types:', data);
            return;
        }
    
        const now = new Date().toLocaleTimeString();

        // Update CO2 value
        document.getElementById('co2').textContent = `${co2} ppm`;

        // Update CO2 chart
        co2Chart.data.labels.push(now);
        co2Chart.data.datasets[0].data.push(co2);

        // Remove old data if more than 10 points
        if (co2Chart.data.labels.length > 10) {
            co2Chart.data.labels.shift();
            co2Chart.data.datasets[0].data.shift();
        }

        // Compute the maximum value of the last 10 data points
        let lastTenValues = co2Chart.data.datasets[0].data; // Array of current data points
        let maxLastTen = Math.max(...lastTenValues); // Find max value in the last 10 points

        // Ensure y-axis minimum is 1000 and increment in steps of 100
        let maxYValue = Math.max(1000, Math.ceil((maxLastTen + 100) / 100) * 100); // Round up to the nearest 100

        // Dynamically update the y-axis range
        co2Chart.options.scales.y = {
            beginAtZero: true,
            min: 0, // Start y-axis at 0 for clarity
            max: maxYValue
        };

        // Update the chart
        co2Chart.update();



        
        // Update O2 value
        document.getElementById('o2').textContent = `${co2} ppm`;

        // Update O2 chart
        o2Chart.data.labels.push(now);
        o2Chart.data.datasets[0].data.push(co2);

        // Remove old data if more than 10 points
        if (o2Chart.data.labels.length > 10) {
            o2Chart.data.labels.shift();
            o2Chart.data.datasets[0].data.shift();
        }

        // Compute the maximum value of the last 10 data points
        let lastTenValues = o2Chart.data.datasets[0].data; // Array of current data points
        let maxLastTen = Math.max(...lastTenValues); // Find max value in the last 10 points

        // Ensure y-axis minimum is 1000 and increment in steps of 100
        let maxYValue = Math.max(1000, Math.ceil((maxLastTen + 100) / 100) * 100); // Round up to the nearest 100

        // Dynamically update the y-axis range
        o2Chart.options.scales.y = {
            beginAtZero: true,
            min: 0, // Start y-axis at 0 for clarity
            max: maxYValue
        };

        // Update the chart
        o2Chart.update();



        // Update CO2 value
        document.getElementById('co2').textContent = `${co2} ppm`;
        // Update Temperature chart
        tempChart.data.labels.push(now);
        tempChart.data.datasets[0].data.push(temperature);
        if (tempChart.data.labels.length > 10) {
            tempChart.data.labels.shift();
            tempChart.data.datasets[0].data.shift();
        }
        tempChart.update();

        // Update CO2 value
        document.getElementById('co2').textContent = `${co2} ppm`;
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
