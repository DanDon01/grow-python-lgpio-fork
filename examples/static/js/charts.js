const charts = new Map();

function createChart(channelId, data) {
    const container = document.createElement('div');
    container.className = 'chart-container';
    container.innerHTML = `<canvas id="chart-${channelId}"></canvas>`;
    document.getElementById('charts-container').appendChild(container);

    const ctx = document.getElementById(`chart-${channelId}`).getContext('2d');
    const alarmAnnotations = data.alarms.map(alarm => ({
        type: 'point',
        xValue: new Date(alarm.timestamp),
        yValue: alarm.value,
        backgroundColor: 'transparent',
        borderColor: 'transparent',
        pointStyle: 'bell',
        pointRadius: 15,
        label: {
            content: '🔔',
            enabled: true
        }
    }));

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.values.map(d => new Date(d.timestamp)),
            datasets: [{
                label: `Sensor ${channelId}`,
                data: data.values.map(d => d.value),
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                annotation: {
                    annotations: alarmAnnotations
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'minute'
                    }
                }
            }
        }
    });
    
    charts.set(channelId, chart);
}

function updateCharts() {
    fetch('/history')
        .then(response => response.json())
        .then(data => {
            for (const [channelId, channelData] of Object.entries(data)) {
                if (!charts.has(channelId)) {
                    createChart(channelId, channelData);
                } else {
                    const chart = charts.get(channelId);
                    chart.data.labels = channelData.values.map(d => new Date(d.timestamp));
                    chart.data.datasets[0].data = channelData.values.map(d => d.value);
                    chart.update();
                }
            }
        });
}

// Initial load and update every 5 seconds
updateCharts();
setInterval(updateCharts, 5000);
