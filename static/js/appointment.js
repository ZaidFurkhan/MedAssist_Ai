document.addEventListener('DOMContentLoaded', () => {
    const dateInput = document.getElementById('appointment_date');
    const timeSelect = document.getElementById('appointment_time');
    const form = document.getElementById('appointment-form');
    const submitBtn = document.getElementById('submit-btn');
    const successAlert = document.getElementById('success-alert');
    const typeSelect = document.getElementById('appointment_type');
    const telehealthNotice = document.getElementById('telehealth-notice');

    // --- Consultation Type Toggle ---
    typeSelect.addEventListener('change', () => {
        if (typeSelect.value === 'Online') {
            telehealthNotice.style.display = 'block';
        } else {
            telehealthNotice.style.display = 'none';
        }
    });

    // --- Smart Logic: Load Context from Session ---
    const contextRaw = sessionStorage.getItem('latest_prediction_context');
    if (contextRaw) {
        const ctx = JSON.parse(contextRaw);
        const triageBanner = document.getElementById('triage-banner');
        const referralContainer = document.getElementById('referral-container');

        // 1. Triage Logic
        const severity = (ctx.severity || "").toLowerCase();
        if (severity.includes('high') || severity.includes('emergency')) {
            triageBanner.classList.add('triage-emergency');
            document.getElementById('triage-title').textContent = "Emergency Priority Detected";
            document.getElementById('triage-desc').textContent = `The AI detected ${ctx.disease} which requires immediate clinical intervention. We recommend visiting the hospital ER immediately.`;
        } else if (severity.includes('moderate') || severity.includes('urgent')) {
            triageBanner.classList.add('triage-urgent');
            triageBanner.style.display = 'flex';
            document.getElementById('triage-title').textContent = "Urgent Care Recommended";
            document.getElementById('triage-desc').textContent = "Based on your symptoms, we recommend seeking care within the next 24-48 hours.";
        }

        // 2. Referral Logic
        if (ctx.summary || (ctx.symptoms && ctx.symptoms.length > 0)) {
            referralContainer.style.display = 'block';
            document.getElementById('referral-summary').textContent = ctx.summary || `Patient presenting with symptoms of ${ctx.disease}.`;

            const symptomsDiv = document.getElementById('referral-symptoms');
            ctx.symptoms.forEach(s => {
                const chip = document.createElement('span');
                chip.className = 's-chip';
                chip.textContent = s;
                symptomsDiv.appendChild(chip);
            });
        }

        // 3. Auto-Select Specialist
        const doctorSelect = document.getElementById('doctor_name');
        const disease = (ctx.disease || "").toLowerCase();

        let targetSpecialty = "";
        if (disease.includes('heart') || disease.includes('hypertension')) targetSpecialty = "cardiologist";
        else if (disease.includes('arthritis') || disease.includes('spondylosis') || disease.includes('osteoarthristis')) targetSpecialty = "orthopedic";
        else if (disease.includes('acne') || disease.includes('psoriasis') || disease.includes('fungal')) targetSpecialty = "dermatologist";
        else if (disease.includes('migraine') || disease.includes('stroke') || disease.includes('brain')) targetSpecialty = "neurologist";

        if (targetSpecialty) {
            for (let i = 0; i < doctorSelect.options.length; i++) {
                if (doctorSelect.options[i].value.toLowerCase().includes(targetSpecialty)) {
                    doctorSelect.selectedIndex = i;
                    break;
                }
            }
        }
    }

    // --- Standard Date/Time Logic ---
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('min', today);

    const timeSlots = [
        "09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM",
        "11:00 AM", "11:30 AM", "01:00 PM", "01:30 PM",
        "02:00 PM", "02:30 PM", "03:00 PM", "04:00 PM"
    ];

    dateInput.addEventListener('change', () => {
        if (dateInput.value) {
            timeSelect.innerHTML = '<option value="">-- Select Time --</option>';
            timeSlots.forEach(slot => {
                timeSelect.innerHTML += `<option value="${slot}">${slot}</option>`;
            });
            timeSelect.disabled = false;
        } else {
            timeSelect.innerHTML = '<option value="">-- Select Date First --</option>';
            timeSelect.disabled = true;
        }
    });

    // --- Form Submission ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        submitBtn.disabled = true;
        submitBtn.innerHTML = 'Booking...';

        // Capture Clinical Context for Email
        const contextRaw = sessionStorage.getItem('latest_prediction_context');
        let clinicalBrief = null;
        if (contextRaw) {
            const ctx = JSON.parse(contextRaw);
            clinicalBrief = {
                summary: ctx.summary,
                symptoms: ctx.symptoms
            };
        }

        const payload = {
            hospital_name: document.getElementById('hospital_name').value,
            doctor_name: document.getElementById('doctor_name').value,
            appointment_date: document.getElementById('appointment_date').value,
            appointment_time: document.getElementById('appointment_time').value,
            patient_name: document.getElementById('patient_name').value,
            patient_phone: document.getElementById('patient_phone').value,
            appointment_type: document.getElementById('appointment_type').value,
            clinical_brief: clinicalBrief
        };

        try {
            const res = await fetch('/api/book_appointment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();

            if (res.ok) {
                successAlert.style.display = 'block';
                form.reset();
                timeSelect.innerHTML = '<option value="">-- Select Date First --</option>';
                timeSelect.disabled = true;
                telehealthNotice.style.display = 'none';

                setTimeout(() => {
                    successAlert.style.display = 'none';
                }, 5000);
            } else {
                alert(data.error || 'Failed to book appointment.');
            }
        } catch (err) {
            console.error(err);
            alert("An error occurred while booking.");
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Confirm Appointment';
        }
    });
});
