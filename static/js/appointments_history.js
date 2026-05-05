document.addEventListener('DOMContentLoaded', async () => {
    const listContainer = document.getElementById('full-appointments-list');

    try {
        const res = await fetch('/api/user/data');
        const data = await res.json();

        if (!data.appointments || data.appointments.length === 0) {
            listContainer.innerHTML = `
                <div class="empty-state-full">
                    <h4>No appointments found</h4>
                    <p>Your scheduled consultations will appear here once you book them while logged in.</p>
                    <p style="font-size: 0.8rem; margin-top: 1rem; color: var(--text-secondary);">
                        * Note: Appointments booked in "Guest Mode" are not linked to your account.
                    </p>
                </div>`;
            return;
        }

        listContainer.innerHTML = data.appointments.map(a => {
            return `
                <div class="appointment-record">
                    <div class="appt-info">
                        <h4>${a.hospital_name}</h4>
                        <p><strong>Doctor:</strong> ${a.doctor_name}</p>
                        <p><strong>Patient:</strong> ${a.patient_name}</p>
                        <p><strong>Mode:</strong> <span style="color: var(--primary); font-weight: 600;">${a.appointment_type || 'In-Person'}</span></p>
                        <span class="status-badge">Confirmed ✅</span>
                    </div>
                    <div class="appt-date-box">
                        <span class="day">${a.appointment_date}</span>
                        <span class="time">${a.appointment_time}</span>
                    </div>
                </div>
             `;
        }).join('');

    } catch (err) {
        listContainer.innerHTML = '<div class="empty-state-full" style="color:#ef4444;">Failed to load appointments.</div>';
    }
});
