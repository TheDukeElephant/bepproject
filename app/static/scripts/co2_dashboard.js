document.addEventListener("DOMContentLoaded", () => {
    const socket = io();

    // Set up chart data
    const data = {
        labels: Array(10).fill(''),  // Labels (time placeholders)
        datasets: [{
            label: 'CO₂ (ppm)',
            data: Array(10).fill(null),  // Initial data points (null for no data)
            borderColor: 'rgba(75, 192, 192, 1)',
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            borderWidth: 1,
            tension: 0.3
        }]
    };

    // Configure the chart
    const config = {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'CO₂ ppm'
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.raw === null ? 'No data' : `${context.raw} ppm`;
                        }
                    }
                }
            }
        }
    };

    // Render the chart
    const ctx = document.getElementById('co2Chart').getContext('2d');
    const co2Chart = new Chart(ctx, config);

    // Listen for CO₂ data updates from the server
    socket.on('update_data', (data) => {
        const co2 = data.co2;
        const now = new Date().toLocaleTimeString();

        // Handle placeholder if no data is received
        const displayValue = isNaN(co2) ? '?' : `${co2} ppm`;

        // Update the chart data (keep only last 10 measurements)
        co2Chart.data.labels.push(now);
        co2Chart.data.datasets[0].data.push(isNaN(co2) ? null : co2);
        if (co2Chart.data.labels.length > 10) {
            co2Chart.data.labels.shift();
            co2Chart.data.datasets[0].data.shift();
        }

        // Update the CO₂ display
        document.getElementById('co2').textContent = displayValue;

        // Update the chart
        co2Chart.update();
    });
});
