function updateTime() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', { hour12: false });
    const dateString = now.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

    document.getElementById('currentTime').textContent = timeString;
    document.getElementById('currentDate').textContent = dateString;
}

// Update time immediately and then every second
if (document.getElementById('currentTime')) {
    updateTime();
    setInterval(updateTime, 1000);
}

async function markAttendance(type) {
    try {
        const response = await fetch('/api/attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ type: type }),
        });

        const data = await response.json();

        if (response.ok) {
            // Show success message (could be a toast)
            // Reload logs
            loadLogs();
            updateStats();
        } else {
            alert(data.error || 'Something went wrong');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to connect to server');
    }
}

async function loadLogs() {
    try {
        const response = await fetch('/api/logs');
        const logs = await response.json();

        const tbody = document.getElementById('logsBody');
        tbody.innerHTML = '';

        logs.forEach(log => {
            const row = document.createElement('tr');
            const date = new Date(log.timestamp);

            row.innerHTML = `
                <td>${date.toLocaleDateString()}</td>
                <td>${date.toLocaleTimeString()}</td>
                <td><span class="status-badge ${log.type === 'check-in' ? 'status-in' : 'status-out'}">${log.type === 'check-in' ? 'Check In' : 'Check Out'}</span></td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading logs:', error);
    }
}

async function updateStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();

        document.getElementById('todayCount').textContent = stats.today_hours;
        document.getElementById('weekCount').textContent = stats.week_hours;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Initial load
if (document.getElementById('logsBody')) {
    loadLogs();
    updateStats();
}
