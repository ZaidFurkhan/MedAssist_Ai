document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const symptomsGrid = document.getElementById('symptoms-grid');
    const searchInput = document.getElementById('symptom-search');
    const countValue = document.getElementById('count-value');
    const predictBtn = document.getElementById('predict-btn');
    const clearBtn = document.getElementById('clear-btn');
    const predictionForm = document.getElementById('prediction-form');
    const loadingState = document.getElementById('loading-symptoms');
    const resultContainer = document.getElementById('result-container');
    const closeResultBtn = document.getElementById('close-result');
    const diseaseName = document.getElementById('disease-name');

    // Landing Page Elements
    const landingPage = document.getElementById('landing-page');
    const mainDashboard = document.getElementById('main-dashboard');
    const getStartedBtn = document.getElementById('get-started-btn');
    const getDemoBtn = document.getElementById('get-demo-btn');

    // Handle Landing Page Transitions
    const urlParams = new URLSearchParams(window.location.search);
    const isDemoMode = urlParams.get('demo') === '1';

    if (getStartedBtn) {
        getStartedBtn.addEventListener('click', () => {
            document.getElementById('login-trigger-btn')?.click();
        });
    }

    // --- Demo Mode Initialization ---
    if (isDemoMode) {
        // Skip landing page immediately
        landingPage.classList.add('hidden');
        mainDashboard.classList.remove('hidden');
        document.body.classList.add('mobile-dashboard-active');
        document.getElementById('demo-badge')?.classList.remove('hidden');

        // Block restricted features with friendly alerts
        const restrictedFeatures = ['nav-hospitals', 'view-more-predictions', 'view-more-appointments'];
        restrictedFeatures.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    alert("This feature requires a registered account. Please sign up to explore history and bookings!");
                }, true); // Use capture to intercept clicks
            }
        });
    }

    if (getDemoBtn) {
        // Handled by <a> tag href="/?demo=1", but adding safety
        getDemoBtn.onclick = () => {
            window.location.href = '/?demo=1';
            return false;
        };
    }

    // Scroll Reveal Logic (Move up for priority)
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.reveal-item').forEach(item => {
        revealObserver.observe(item);
    });

    // Handle Mobile FAB
    document.getElementById('mobile-chat-fab')?.addEventListener('click', () => {
        document.getElementById('nav-chat')?.click();

        // Hide FAB when chat is open on mobile
        const fab = document.getElementById('mobile-chat-fab');
        if (fab && window.innerWidth <= 768) {
            fab.style.display = 'none';
        }
    });

    // Close mobile chat button
    document.getElementById('close-chat-mobile')?.addEventListener('click', () => {
        // Just switch back to symptoms or wherever we were
        document.getElementById('nav-symptoms').click();

        // Show FAB again
        const fab = document.getElementById('mobile-chat-fab');
        if (fab) fab.style.display = 'flex';
    });

    let allSymptoms = [];
    const selectedSymptomsSet = new Set();

    // Helper: Format symptom string (nodal_skin_eruptions -> Nodal Skin Eruptions)
    function formatSymptomName(str) {
        return str
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    // 1. Fetch symptoms from backend
    async function loadSymptoms() {
        if (!loadingState) return;
        try {
            const response = await fetch('/api/symptoms');
            const data = await response.json();

            if (data.error) throw new Error(data.error);

            allSymptoms = data.symptoms;
            renderSymptoms(allSymptoms);

            loadingState.classList.add('hidden');
        } catch (error) {
            console.error("Error loading symptoms:", error);
            loadingState.innerHTML = `
                <div style="color: #ef4444; margin-bottom: 1rem;">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="8" x2="12" y2="12"></line>
                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                    </svg>
                </div>
                <p style="color: #ef4444; font-weight: 500;">Failed to load symptoms database. Is the Flask server running?</p>
            `;
        }
    }

    // 2. Render symptoms to the DOM
    function renderSymptoms(symptomsToRender) {
        if (!symptomsGrid) return;
        symptomsGrid.innerHTML = '';

        if (symptomsToRender.length === 0) {
            symptomsGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; color: var(--text-secondary); padding: 2rem;">
                    No symptoms matched your search. Try different keywords.
                </div>
            `;
            return;
        }

        symptomsToRender.forEach((symptom) => {
            const id = `symptom-${symptom}`;
            const formattedName = formatSymptomName(symptom);

            const div = document.createElement('div');
            div.className = 'symptom-item';

            const isChecked = selectedSymptomsSet.has(symptom) ? 'checked' : '';
            div.innerHTML = `
                <input type="checkbox" id="${id}" name="symptoms" value="${symptom}" class="symptom-checkbox" ${isChecked}>
                <label for="${id}" class="symptom-label">${formattedName}</label>
            `;

            symptomsGrid.appendChild(div);
        });

        attachCheckboxListeners();
    }

    // 3. Search / Filter logic
    searchInput?.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase().trim();
        if (!term) {
            renderSymptoms(allSymptoms);
            return;
        }
        const filtered = allSymptoms.filter(s => {
            const rawMatch = s.toLowerCase().includes(term);
            const displayMatch = formatSymptomName(s).toLowerCase().includes(term);
            return rawMatch || displayMatch;
        });
        renderSymptoms(filtered);
    });

    // 4. Update count and button active state
    function attachCheckboxListeners() {
        const checkboxes = document.querySelectorAll('.symptom-checkbox');

        checkboxes.forEach(box => {
            box.removeEventListener('change', handleCheckboxChange); // prevent dupes
            box.addEventListener('change', handleCheckboxChange);
        });
    }

    function handleCheckboxChange(e) {
        const checkbox = e.target;
        if (checkbox.checked) {
            selectedSymptomsSet.add(checkbox.value);
        } else {
            selectedSymptomsSet.delete(checkbox.value);
        }

        countValue.textContent = selectedSymptomsSet.size;

        if (selectedSymptomsSet.size > 0) {
            predictBtn.disabled = false;
            clearBtn.disabled = false;
        } else {
            predictBtn.disabled = true;
            clearBtn.disabled = true;
        }
    }

    // 5. Clear Form logic
    clearBtn.addEventListener('click', () => {
        // Clear the Set
        selectedSymptomsSet.clear();

        // Uncheck all visible checkboxes
        const checkboxes = document.querySelectorAll('.symptom-checkbox');
        checkboxes.forEach(box => {
            box.checked = false;
        });

        // Clear Dropdowns
        document.getElementById('age-select').value = '';
        document.getElementById('gender-select').value = '';

        // Update UI counters and buttons
        countValue.textContent = '0';
        predictBtn.disabled = true;
        clearBtn.disabled = true;

        // Hide post-prediction tabs (Except Hospitals which is now always available)
        document.getElementById('nav-diagnosis').classList.add('hidden');

        // Switch back to symptoms tab
        document.getElementById('nav-symptoms').click();
    });

    // Initialize Clear Button State
    clearBtn.disabled = true;

    // 6. Submit Form to API
    predictionForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Gather selected symptoms from Set (not just DOM, because search might hide them)
        const selectedSymptoms = Array.from(selectedSymptomsSet);

        if (selectedSymptoms.length === 0) return;

        // UI Loading state
        const originalBtnText = predictBtn.innerHTML;
        predictBtn.disabled = true;
        clearBtn.disabled = true;
        predictBtn.innerHTML = `
            <div style="width: 20px; height: 20px; border: 2px solid white; border-top-color: transparent; border-radius: 50%; animation: spin 1s linear infinite;"></div>
            <span>Analyzing...</span>
        `;

        const age = document.getElementById('age-select').value;
        const gender = document.getElementById('gender-select').value;

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symptoms: selectedSymptoms, age: age, gender: gender })
            });

            const data = await response.json();

            if (!response.ok) throw new Error(data.error || 'Server error occurred');

            // Show Result Overlay
            diseaseName.textContent = data.prediction;
            currentPrediction = data.prediction; // Share with chatbot

            // Render Top Predictions as Master List
            const listContainer = document.getElementById('conditions-list-container');
            const detailsWrapper = document.getElementById('details-container-wrapper');
            const emptyState = document.getElementById('details-empty-state');
            const selectedHeader = document.getElementById('selected-diagnosis-header');

            listContainer.innerHTML = ''; // clear old

            if (data.top_predictions && data.top_predictions.length > 0) {
                data.top_predictions.forEach((p, index) => {
                    const card = document.createElement('div');
                    card.className = `condition-card ${index === 0 ? 'active' : ''}`;
                    card.innerHTML = `
                        <h5 style="margin-bottom: 0.25rem;">${p.disease}</h5>
                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.25rem;">
                            <span style="color: var(--text-secondary);">Match Confidence</span>
                            <span style="font-weight: 700; color: var(--primary-color);">${p.probability}%</span>
                        </div>
                        <div style="width: 100%; height: 6px; background: var(--primary-light); border-radius: 4px; overflow: hidden; margin-top: 0.5rem;">
                            <div style="height: 100%; width: ${p.probability}%; background: var(--primary-color); border-radius: 4px;"></div>
                        </div>
                    `;

                    // Click handler for details view
                    card.addEventListener('click', () => {
                        // styling
                        document.querySelectorAll('.condition-card').forEach(c => c.classList.remove('active'));
                        card.classList.add('active');

                        // update details pane
                        emptyState.style.display = 'none';
                        selectedHeader.style.display = 'flex';
                        detailsWrapper.style.display = 'block';

                        document.getElementById('disease-name').textContent = p.disease;
                        currentPrediction = p.disease; // update chatbot context

                        fetchDiseaseDetails(p.disease);
                    });

                    listContainer.appendChild(card);
                });

                // Auto-select the top result
                const firstCard = listContainer.querySelector('.condition-card');
                if (firstCard) firstCard.click();
            }

            // Reveal blocked tabs
            document.getElementById('nav-diagnosis').classList.remove('hidden');
            if (!window._isGuestMode) {
                document.getElementById('nav-hospitals').classList.remove('hidden');
            }

            // Switch to Diagnosis tab
            document.getElementById('nav-diagnosis').click();

            // Try fetching nearby hospitals automatically (with context)
            requestLocation(data.prediction);

        } catch (error) {
            console.error(error);
            alert(`Prediction Failed: ${error.message}`);
        } finally {
            // Restore button
            predictBtn.innerHTML = originalBtnText;
            predictBtn.disabled = false; // Note: they can predict again!
            clearBtn.disabled = false;
        }
    });

    // Initialize Payload
    loadSymptoms();

    // --- Hospital & Geolocation Logic ---
    function fetchHospitals(lat, lon, diseaseName = '') {
        const hospitalsContainer = document.getElementById('hospitals-container');
        const hospitalsList = document.getElementById('hospitals-list');
        hospitalsContainer.classList.remove('hidden');

        // Show loading state
        hospitalsList.innerHTML = `
            <div class="loading-hospitals">
                <div class="spinner" style="width:24px;height:24px;border-width:3px;margin: 0 auto 10px auto;"></div>
                <p style="text-align:center;font-size:0.9rem;color:var(--text-secondary);">Locating your position...</p>
            </div>
        `;

        const loadingText = hospitalsList.querySelector('p');
        const hospitalSteps = [
            "Scanning for healthcare facilities...",
            "Retrieving contact details..."
        ];

        let step = 0;
        const hInterval = setInterval(() => {
            if (step < hospitalSteps.length) {
                loadingText.textContent = hospitalSteps[step];
                step++;
            }
        }, 2000);

        fetch(`/api/hospitals?lat=${lat}&lon=${lon}&disease=${encodeURIComponent(diseaseName)}`)
            .then(res => res.json())
            .then(data => {
                if (data.error) throw new Error(data.error);

                clearInterval(hInterval);

                if (!data.hospitals || data.hospitals.length === 0) {
                    hospitalsList.innerHTML = '<div class="loading-hospitals">No hospitals found nearby.</div>';
                    return;
                }

                let html = '';
                if (data.target_specialty) {
                    html += `<div class="hospital-specialty-notice">💡 Prioritizing facilities with <b>${data.target_specialty}</b> departments for ${diseaseName}.</div>`;
                }

                data.hospitals.forEach(h => {
                    const badge = h.is_specialized ? `<span class="hospital-recommended-badge">Recommended</span>` : '';

                    const mapQuery = encodeURIComponent(`${h.name} ${h.lat},${h.lon}`);
                    const appointmentBtn = window._isGuestMode
                        ? `<button onclick="alert('Please login or create an account to book appointments.')" class="hospital-book-btn disabled">🔒 Login to Book</button>`
                        : `<button onclick="window.location.href = '/appointment?hospital=' + encodeURIComponent('${h.name.replace(/'/g, "\\'").replace(/"/g, "&quot;")}')" class="hospital-book-btn">📅 Book Appointment</button>`;
                    html += `
                        <div class="hospital-card">
                            <h5 class="hospital-name">${h.name} ${badge}</h5>
                            <p class="hospital-address">📍 ${h.address}</p>
                            ${h.phone !== 'Phone not available' ? `<p class="hospital-phone">📞 ${h.phone}</p>` : '<div class="hospital-phone placeholder"></div>'}
                            
                            <div class="hospital-card-actions">
                                ${appointmentBtn}
                                <a href="https://www.google.com/maps/search/?api=1&query=${mapQuery}" target="_blank" class="hospital-map-link">
                                    🗺️ View on Map ↗
                                </a>
                            </div>
                        </div>
                    `;
                });
                hospitalsList.innerHTML = html;
            })
            .catch(err => {
                console.error(err);
                clearInterval(hInterval);
                hospitalsList.innerHTML = '<div class="loading-hospitals" style="color:#ef4444;">Failed to load hospitals.</div>';
            });
    }

    function requestLocation(diseaseName = '') {
        if ("geolocation" in navigator) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    fetchHospitals(position.coords.latitude, position.coords.longitude, diseaseName);
                },
                (error) => {
                    console.warn("Geolocation blocked or failed.", error);
                    const hospitalsContainer = document.getElementById('hospitals-container');
                    hospitalsContainer.classList.remove('hidden');
                    document.getElementById('hospitals-list').innerHTML = '<div class="loading-hospitals">Location access needed to find nearby hospitals.</div>';
                }
            );
        }
    }

    // --- Tab Switching Logic ---
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            const target = btn.getAttribute('data-target');
            document.getElementById(target).classList.add('active');

            // If hospitals tab is clicked and it's currently empty, trigger location request
            if (target === 'tab-hospitals') {
                const hospitalsList = document.getElementById('hospitals-list');
                // Check if it's the default loading state or empty
                if (hospitalsList.querySelector('.loading-hospitals')) {
                    requestLocation();
                }
            }
        });
    });

    // --- Disease Info Intelligence Logic ---
    async function fetchDiseaseDetails(diseaseName) {
        const loadingDiv = document.getElementById('disease-details-loading');
        const contentDiv = document.getElementById('disease-details-content');

        loadingDiv.classList.remove('hidden');
        contentDiv.classList.add('hidden');

        // Dynamic loading text to improve perceived performance
        const loadingText = loadingDiv.querySelector('p');
        const originalText = loadingText.textContent;
        const loadingSteps = [
            "Analyzing pathology for " + diseaseName + "...",
            "Consulting medical literature...",
            "Generating dietary guidelines...",
            "Finalizing comprehensive report..."
        ];

        let step = 0;
        const progressInterval = setInterval(() => {
            if (step < loadingSteps.length) {
                loadingText.textContent = loadingSteps[step];
                step++;
            }
        }, 2500);

        try {
            const res = await fetch(`/api/disease-info?disease=${encodeURIComponent(diseaseName)}`);
            const data = await res.json();

            if (data.error) throw new Error(data.error);

            document.getElementById('detail-description').textContent = data.description || 'No description available.';

            // Handle severity badge
            const severityEl = document.getElementById('disease-severity');
            if (data.severity) {
                const sev = data.severity.toLowerCase();
                severityEl.textContent = data.severity;
                severityEl.className = 'severity-badge';

                if (sev.includes('low')) severityEl.classList.add('severity-low');
                else if (sev.includes('moderate')) severityEl.classList.add('severity-moderate');
                else if (sev.includes('high')) severityEl.classList.add('severity-high');
                else if (sev.includes('critical')) severityEl.classList.add('severity-critical');
                else severityEl.classList.add('severity-moderate');

                severityEl.classList.remove('hidden');
            } else {
                severityEl.classList.add('hidden');
            }

            const precList = document.getElementById('detail-precautions');
            precList.innerHTML = '';
            (data.precautions || ['No specific precautions listed.']).forEach(p => {
                const li = document.createElement('li');
                li.textContent = p;
                precList.appendChild(li);
            });

            const dietList = document.getElementById('detail-diet');
            dietList.innerHTML = '';
            (data.diet || ['No specific diet listed.']).forEach(d => {
                const li = document.createElement('li');
                li.textContent = d;
                dietList.appendChild(li);
            });

            // --- Text-to-Speech (TTS) Logic ---
            const readAloudBtn = document.getElementById('read-aloud-btn');
            if (readAloudBtn) {
                // Ensure existing speech is stopped when switching diseases
                window.speechSynthesis.cancel();

                // Define the click handler dynamically for this specific prediction
                readAloudBtn.onclick = () => {
                    if (window.speechSynthesis.speaking) {
                        // Toggle play/stop if already speaking
                        window.speechSynthesis.cancel();
                        readAloudBtn.innerHTML = `
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                                <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                            </svg>
                            Read
                        `;
                    } else {
                        const textToRead = document.getElementById('detail-description').textContent;
                        const utterance = new SpeechSynthesisUtterance(textToRead);

                        // Try to use a natural English voice if available
                        const voices = window.speechSynthesis.getVoices();
                        const englishVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Google') || v.name.includes('Natural')));
                        if (englishVoice) utterance.voice = englishVoice;

                        utterance.rate = 1.0;
                        utterance.pitch = 1.0;

                        // Change button state to indicate reading
                        readAloudBtn.innerHTML = `
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="6" y="4" width="4" height="16"></rect>
                                <rect x="14" y="4" width="4" height="16"></rect>
                            </svg>
                            Stop
                        `;

                        // Reset button when speech finishes naturally
                        utterance.onend = () => {
                            readAloudBtn.innerHTML = `
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                                    <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                                </svg>
                                Read
                            `;
                        };

                        window.speechSynthesis.speak(utterance);
                    }
                };
            }

            clearInterval(progressInterval);
            loadingText.textContent = originalText;
            loadingDiv.classList.add('hidden');
            contentDiv.classList.remove('hidden');
        } catch (error) {
            console.error("Failed to fetch disease details intel:", error);
            clearInterval(progressInterval);
            loadingText.textContent = originalText;
            loadingDiv.innerHTML = '<p style="text-align:center;color:#ef4444;font-size:0.9rem;">AI intel temporarily unavailable.</p>';
        }
    }

    // --- Chatbot Logic ---
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatSendBtn = document.getElementById('chat-send-btn');
    const chatMicBtn = document.getElementById('chat-mic-btn');

    let chatHistory = [];
    let currentPrediction = null;

    // --- Voice Search Logic ---
    let recognition;
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onstart = function () {
            chatMicBtn.classList.add('recording');
            chatInput.placeholder = "Listening...";
        };

        recognition.onresult = function (event) {
            const transcript = event.results[0][0].transcript;
            chatInput.value = transcript;
            chatSendBtn.disabled = false;

            // Optionally, auto-submit the form after speaking:
            // chatForm.dispatchEvent(new Event('submit'));
        };

        recognition.onerror = function (event) {
            console.error('Speech recognition error:', event.error);
            chatMicBtn.classList.remove('recording');
            chatInput.placeholder = "Message AI Assistant...";
        };

        recognition.onend = function () {
            chatMicBtn.classList.remove('recording');
            chatInput.placeholder = "Message AI Assistant...";
        };

        chatMicBtn.addEventListener('click', () => {
            if (chatMicBtn.classList.contains('recording')) {
                recognition.stop();
            } else {
                try {
                    recognition.start();
                } catch (e) {
                    console.error(e);
                }
            }
        });
    } else {
        if (chatMicBtn) chatMicBtn.style.display = 'none'; // Hide if not supported
    }

    chatInput.addEventListener('input', (e) => {
        chatSendBtn.disabled = e.target.value.trim().length === 0;
    });

    function addMessage(content, role) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}-msg`;

        if (role === 'assistant' && typeof marked !== 'undefined') {
            msgDiv.innerHTML = marked.parse(content);
        } else {
            msgDiv.textContent = content;
        }

        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = chatInput.value.trim();
        if (!text) return;

        // Add user message
        addMessage(text, 'user');
        chatHistory.push({ role: 'user', content: text });
        chatInput.value = '';
        chatSendBtn.disabled = true;

        // Show typing indicator
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant-msg';
        typingDiv.innerHTML = '<div style="width: 15px; height: 15px; border: 2px solid var(--primary-color); border-top-color: transparent; border-radius: 50%; animation: spin 1s linear infinite;"></div>';
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            // Build payload injected with system context if prediction exists
            let payload = [...chatHistory];
            // Always prepend strong system context to the payload
            const diagContext = currentPrediction ? ` The user's AI-predicted diagnosis is: ${currentPrediction}.` : ``;
            payload.unshift({
                role: "system",
                content: `You are a helpful, calming, and reliable medical AI assistant.${diagContext} You must stay strictly on the topic of healthcare. DO NOT provide false information; if unsure, simply state that you do not know. 
To avoid causing panic while remaining safe, ALWAYS structure your medical advice using these exactly 4 sections:
1. **Possible condition** (frame this as a possibility, not a definite diagnosis)
2. **What to do now** (calm, actionable home-care or next steps)
3. **When to see a doctor** (routine check-up guidelines)
4. **Emergency warning signs** (objective symptoms that require immediate care)
Keep your tone balanced, user-friendly, and concise.`
            });

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: payload })
            });
            const data = await response.json();

            if (typingDiv.parentNode) typingDiv.remove();

            if (data.error) throw new Error(data.error);

            const reply = data.response;
            if (!reply || reply.trim() === '') {
                throw new Error("Received empty response from the AI assistant.");
            }
            addMessage(reply, 'assistant');
            chatHistory.push({ role: 'assistant', content: reply });

        } catch (err) {
            console.error(err);
            if (typingDiv.parentNode) typingDiv.remove();
            addMessage('Sorry, I encountered an error connecting to the AI server.', 'assistant');
            // Remove failed user message from history so they can try again
            chatHistory.pop();
        }
    });

    // --- Authentication & Account Logic ---
    const authModal = document.getElementById('auth-modal');
    const loginTriggerBtn = document.getElementById('login-trigger-btn');
    const closeAuthModal = document.getElementById('close-auth-modal');
    const loginView = document.getElementById('login-view');
    const registerView = document.getElementById('register-view');
    const verifyView = document.getElementById('verify-view');
    const switchToRegister = document.getElementById('switch-to-register');
    const switchToLogin = document.getElementById('switch-to-login');

    if (loginTriggerBtn) {
        loginTriggerBtn.addEventListener('click', () => {
            authModal.style.display = 'flex';
            showView('login');
        });
    }

    // --- Sidebar Logic ---
    const userSidebar = document.getElementById('user-sidebar');
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const userProfileBtn = document.getElementById('user-profile-btn');
    const closeSidebarBtn = document.getElementById('close-sidebar');

    function toggleSidebar(show) {
        if (show) {
            userSidebar.classList.add('active');
            sidebarOverlay.classList.add('active');
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
            loadUserHistory();
        } else {
            userSidebar.classList.remove('active');
            sidebarOverlay.classList.remove('active');
            document.body.style.overflow = ''; // Restore scrolling
        }
    }

    if (userProfileBtn) {
        userProfileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleSidebar(true);
        });
    }

    if (closeSidebarBtn) {
        closeSidebarBtn.addEventListener('click', () => toggleSidebar(false));
    }

    // Sidebar Click-Away Logic
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', () => toggleSidebar(false));
    }

    // --- Accordion Logic ---
    const accordions = document.querySelectorAll('.accordion-toggle');
    accordions.forEach(toggle => {
        toggle.addEventListener('click', () => {
            const section = toggle.closest('.sidebar-section');
            section.classList.toggle('active');
        });
    });

    if (authModal) {
        // Prevent clicking user-profile from closing modal if logic conflicts
    }

    if (closeAuthModal) {
        closeAuthModal.addEventListener('click', () => {
            authModal.style.display = 'none';
        });
    }

    window.addEventListener('click', (e) => {
        if (e.target === authModal) authModal.style.display = 'none';
    });

    function showView(viewName) {
        loginView.classList.add('hidden');
        registerView.classList.add('hidden');
        verifyView.classList.add('hidden');

        if (viewName === 'login') loginView.classList.remove('hidden');
        else if (viewName === 'register') registerView.classList.remove('hidden');
        else if (viewName === 'verify') verifyView.classList.remove('hidden');
    }

    switchToRegister.addEventListener('click', (e) => { e.preventDefault(); showView('register'); });
    switchToLogin.addEventListener('click', (e) => { e.preventDefault(); showView('login'); });

    // Handle Login
    document.getElementById('login-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error);

            location.reload(); // Reload to update UI with user session
        } catch (err) {
            alert(err.message);
        }
    });

    // Handle Register
    document.getElementById('register-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('register-email')?.value;
        const password = document.getElementById('register-password')?.value;

        try {
            const res = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            let data;
            const contentType = res.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                data = await res.json();
            } else {
                const textError = await res.text();
                throw new Error(`Server Error (${res.status}): ${textError.substring(0, 100)}...`);
            }

            if (!res.ok) throw new Error(data.error || "Registration failed.");

            alert(data.message);
            if (data.demo_code) console.log("Demo Verification Code:", data.demo_code);

            // Store email for verification view
            document.getElementById('verify-form').dataset.email = email;
            showView('verify');
        } catch (err) {
            alert(err.message);
        }
    });

    // Handle Verify
    document.getElementById('verify-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = e.target.dataset.email;
        const code = document.getElementById('verify-code')?.value;

        try {
            const res = await fetch('/api/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, code })
            });

            let data;
            const contentType = res.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                data = await res.json();
            } else {
                const textError = await res.text();
                throw new Error(`Server Error (${res.status}): ${textError.substring(0, 100)}...`);
            }

            if (!res.ok) throw new Error(data.error || "Verification failed.");

            alert(data.message);
            showView('login');
        } catch (err) {
            alert(err.message);
        }
    });

    // Handle Logout
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            await fetch('/api/logout', { method: 'POST' });
            location.reload();
        });
    }

    // --- History Loading Logic ---
    async function loadUserHistory() {
        const predList = document.getElementById('sidebar-predictions-list');
        const apptList = document.getElementById('sidebar-appointments-list');
        const viewMorePreds = document.getElementById('view-more-predictions');
        const viewMoreAppts = document.getElementById('view-more-appointments');

        if (!predList || !apptList) return;

        try {
            const res = await fetch('/api/user/data');
            if (!res.ok) return;

            const data = await res.json();

            // Predictions (Limit to 3)
            if (data.predictions && data.predictions.length > 0) {
                predList.innerHTML = '';
                const itemsToShow = data.predictions.slice(0, 3);
                itemsToShow.forEach(p => {
                    const date = new Date(p.created_at).toLocaleDateString('en-US', {
                        month: 'short', day: 'numeric', year: 'numeric'
                    });
                    const item = document.createElement('div');
                    item.className = 'history-item-sidebar';
                    item.innerHTML = `
                        <span class="disease">${p.predicted_disease}</span>
                        <span class="date">${date}</span>
                    `;
                    predList.appendChild(item);
                });

                viewMorePreds.classList.remove('hidden');
            } else {
                predList.innerHTML = '<p class="empty-text-sidebar">No recent predictions.</p>';
                viewMorePreds.classList.remove('hidden');
            }

            // Appointments (Limit to 3)
            if (data.appointments && data.appointments.length > 0) {
                apptList.innerHTML = '';
                const itemsToShow = data.appointments.slice(0, 3);
                itemsToShow.forEach(a => {
                    const item = document.createElement('div');
                    item.className = 'history-item-sidebar';
                    item.innerHTML = `
                        <span class="disease">${a.doctor_name}</span>
                        <span class="date">${a.hospital_name}</span>
                        <div class="date" style="margin-top:2px;">📅 ${a.appointment_date} at ${a.appointment_time}</div>
                    `;
                    apptList.appendChild(item);
                });

                viewMoreAppts.classList.remove('hidden');
            } else {
                apptList.innerHTML = '<p class="empty-text-sidebar">No upcoming appointments.</p>';
                viewMoreAppts.classList.remove('hidden');
            }
        } catch (error) {
            console.error("Error loading history:", error);
        }
    }

    // --- Logout Logic ---
    document.querySelectorAll('#logout-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                const response = await fetch('/api/logout', { method: 'POST' });
                if (response.ok) {
                    window.location.href = '/';
                } else {
                    console.error("Logout failed", await response.text());
                }
            } catch (err) {
                console.error("Logout error:", err);
            }
        });
    });

    // Initial load if user is already logged in
    if (document.getElementById('user-profile-btn')) {
        loadUserHistory();
    }

    // --- Mobile Redesign Interactive Logic ---
    const mobileChatFab = document.getElementById('mobile-chat-fab');
    const closeChatMobile = document.getElementById('close-chat-mobile');
    const sidebarBackBtn = document.getElementById('sidebar-back-btn');

    // Sidebar "Back to Dashboard" logic
    sidebarBackBtn?.addEventListener('click', () => {
        toggleSidebar(false);
    });

    // Floating Chat FAB logic
    mobileChatFab?.addEventListener('click', () => {
        document.body.classList.add('mobile-chat-active');
        document.getElementById('nav-chat')?.click();

        // Auto-focus chat input on mobile
        setTimeout(() => {
            document.getElementById('chat-input')?.focus();
        }, 300);
    });

    // Mobile Chat "Back to Dashboard" logic
    closeChatMobile?.addEventListener('click', () => {
        document.body.classList.remove('mobile-chat-active');

        // Explicitly restore Symptoms tab visibility to avoid "empty page" state
        const symptomsTab = document.getElementById('nav-symptoms');
        if (symptomsTab) {
            symptomsTab.click();
            // Ensure the content is active even if click() had issues
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById('tab-symptoms')?.classList.add('active');
        }
    });

    // --- Showcase Slider Logic ---
    const slides = document.querySelectorAll('.showcase-slide');
    const dots = document.querySelectorAll('.nav-dot');
    let currentSlide = 0;
    let slideInterval;

    function showSlide(index) {
        if (slides.length === 0) return;

        slides.forEach(s => s.classList.remove('active'));
        dots.forEach(d => d.classList.remove('active'));

        slides[index].classList.add('active');
        dots[index].classList.add('active');
        currentSlide = index;
    }

    function nextSlide() {
        let next = (currentSlide + 1) % slides.length;
        showSlide(next);
    }

    function startSlideTimer() {
        stopSlideTimer();
        slideInterval = setInterval(nextSlide, 5000);
    }

    function stopSlideTimer() {
        if (slideInterval) clearInterval(slideInterval);
    }

    dots.forEach(dot => {
        dot.addEventListener('click', () => {
            const target = parseInt(dot.dataset.target);
            showSlide(target);
            startSlideTimer(); // Reset timer on manual click
        });
    });

    if (slides.length > 0) {
        startSlideTimer();
    }

    // Audit: Handle window resizing to ensure mobile classes are cleaned up if switching to desktop
    window.addEventListener('resize', () => {
        if (window.innerWidth > 600) {
            document.body.classList.remove('mobile-chat-active');
        }
    });
});
