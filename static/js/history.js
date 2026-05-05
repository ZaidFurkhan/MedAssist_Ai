document.addEventListener('DOMContentLoaded', async () => {
    const listContainer = document.getElementById('full-history-list');

    try {
        const res = await fetch('/api/user/data');
        const data = await res.json();

        if (!data.predictions || data.predictions.length === 0) {
            listContainer.innerHTML = '<div class="empty-state-full"><h4>No history found</h4><p>Your disease predictions will appear here once you use the system.</p></div>';
            return;
        }

        listContainer.innerHTML = data.predictions.map(p => {
            const date = new Date(p.created_at).toLocaleString('en-US', {
                month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit'
            });

            return `
                <div class="history-record">
                    <div class="record-head">
                        <span class="record-disease">${p.predicted_disease}</span>
                        <span class="record-date">${date}</span>
                    </div>
                    <div class="record-symptoms">
                        <strong>Symptoms:</strong> ${p.symptoms.join(', ').replace(/_/g, ' ')}
                    </div>
                </div>
             `;
        }).join('');

    } catch (err) {
        listContainer.innerHTML = '<div class="empty-state-full" style="color:#ef4444;">Failed to load history.</div>';
    }
});
