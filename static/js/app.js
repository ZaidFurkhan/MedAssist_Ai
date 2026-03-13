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
        try {
            const response = await fetch('/api/symptoms');
            const data = await response.json();
            
            if (data.error) throw new Error(data.error);
            
            allSymptoms = data.symptoms;
            renderSymptoms(allSymptoms);
            
            // Hide loading state once done
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
        symptomsGrid.innerHTML = ''; // Clear current grid
        
        if (symptomsToRender.length === 0) {
            symptomsGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; color: var(--text-secondary); padding: 2rem;">
                    No symptoms matched your search. Try different keywords.
                </div>
            `;
            return;
        }

        symptomsToRender.forEach((symptom) => {
            const id = `symptom-${symptom}`; // Ensure unique ID
            const formattedName = formatSymptomName(symptom);

            const div = document.createElement('div');
            div.className = 'symptom-item';

            // Custom UI checkbox block
            const isChecked = selectedSymptomsSet.has(symptom) ? 'checked' : '';
            div.innerHTML = `
                <input type="checkbox" id="${id}" name="symptoms" value="${symptom}" class="symptom-checkbox" ${isChecked}>
                <label for="${id}" class="symptom-label">
                    ${formattedName}
                </label>
            `;
            
            symptomsGrid.appendChild(div);
        });

        // Re-attach listener to new checkboxes
        attachCheckboxListeners();
    }

    // 3. Search / Filter logic
    searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase().trim();
        
        if (!term) {
            renderSymptoms(allSymptoms);
            return;
        }

        // Filter: match either the raw value or the formatted value
        const filtered = allSymptoms.filter(s => {
            const rawMatch = s.toLowerCase().includes(term);
            const formattedMatch = formatSymptomName(s).toLowerCase().includes(term);
            return rawMatch || formattedMatch;
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

        // Hide post-prediction tabs
        document.getElementById('nav-diagnosis').classList.add('hidden');
        document.getElementById('nav-hospitals').classList.add('hidden');
        
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
            document.getElementById('nav-hospitals').classList.remove('hidden');

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
                    html += `<div style="font-size:0.85rem;color:var(--primary-color);margin-bottom:1rem;background:#e0e7ff;padding:0.5rem 1rem;border-radius:8px;">💡 Prioritizing facilities with <b>${data.target_specialty}</b> departments for ${diseaseName}.</div>`;
                }
                
                data.hospitals.forEach(h => {
                    const badge = h.is_specialized ? `<span style="background:var(--primary-color);color:white;font-size:0.7rem;padding:2px 8px;border-radius:12px;margin-left:8px;vertical-align:middle;">Recommended</span>` : '';
                    
                    const mapQuery = encodeURIComponent(`${h.name} ${h.lat},${h.lon}`);
                    html += `
                        <div class="hospital-card" style="background:var(--bg-color);border:1px solid var(--border-color);border-radius:12px;padding:1.25rem;margin-bottom:1rem;position:relative;">
                            <h5 style="color:var(--primary-color);font-size:1.05rem;margin-bottom:0.5rem;margin-top:0;">
                                ${h.name} ${badge}
                            </h5>
                            <p style="font-size:0.9rem;color:var(--text-secondary);margin-bottom:0.25rem;">📍 ${h.address}</p>
                            ${h.phone !== 'Phone not available' ? `<p style="font-size:0.9rem;color:var(--text-secondary);margin-bottom:1rem;">📞 ${h.phone}</p>` : '<div style="margin-bottom: 1rem;"></div>'}
                            
                            <div style="display: flex; gap: 1rem; align-items: center; margin-top: auto; flex-wrap: wrap;">
                                <button onclick="window.open('/appointment?hospital=' + encodeURIComponent('${h.name.replace(/'/g, "\\'")}'), '_blank')" style="background: var(--primary-color); color: white; border: none; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 500; cursor: pointer; font-size: 0.9rem; transition: background 0.2s ease;">
                                    📅 Book Appointment
                                </button>
                                <a href="https://www.google.com/maps/search/?api=1&query=${mapQuery}" target="_blank" style="font-size:0.85rem;color:var(--primary-color);text-decoration:none;font-weight:600;">
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

        recognition.onstart = function() {
            chatMicBtn.classList.add('recording');
            chatInput.placeholder = "Listening...";
        };

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            chatInput.value = transcript;
            chatSendBtn.disabled = false;
            
            // Optionally, auto-submit the form after speaking:
            // chatForm.dispatchEvent(new Event('submit'));
        };

        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            chatMicBtn.classList.remove('recording');
            chatInput.placeholder = "Message AI Assistant...";
        };

        recognition.onend = function() {
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
            if (currentPrediction && payload.length === 1) {
                // Prepend context on first message
                payload.unshift({
                    role: "user",
                    content: `System Context: The user was just diagnosed with ${currentPrediction}. Act as a helpful medical AI assistant. Answer their questions intelligently. Keep responses concise.`
                });
            }

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: payload })
            });
            const data = await response.json();
            
            chatMessages.removeChild(typingDiv);

            if (data.error) throw new Error(data.error);
            
            const reply = data.response;
            addMessage(reply, 'assistant');
            chatHistory.push({ role: 'assistant', content: reply });

        } catch (err) {
            console.error(err);
            chatMessages.removeChild(typingDiv);
            addMessage('Sorry, I encountered an error connecting to the AI server.', 'assistant');
            // Remove failed user message from history so they can try again
            chatHistory.pop();
        }
    });
});
