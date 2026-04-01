document.addEventListener('DOMContentLoaded', () => {
    const textInput = document.getElementById('textInput');
    const translateTextBtn = document.getElementById('translateTextBtn');

    const micBtn = document.getElementById('micBtn');
    const camBtn = document.getElementById('camBtn');
    const speakerBtn = document.getElementById('speakerBtn');

    const statusText = document.getElementById('statusText');

    const signPanel = document.getElementById('signPanel');
    const signPlaceholder = document.getElementById('signPlaceholder');
    const signOutput = document.getElementById('signOutput');
    const signPlayerVideo = document.getElementById('signPlayerVideo');
    const signPlayerImage = document.getElementById('signPlayerImage');
    const signMediaEmpty = document.getElementById('signMediaEmpty');
    const signMediaLabel = document.getElementById('signMediaLabel');
    const signGlossLine = document.getElementById('signGlossLine');
    const signSequence = document.getElementById('signSequence');

    const cameraContainer = document.getElementById('cameraContainer');
    const webcamView = document.getElementById('webcamView');
    const cameraCanvas = document.getElementById('cameraCanvas');

    let isRecordingAudio = false;
    let recognition = null;

    let isCameraActive = false;
    let webcamStream = null;
    let cameraInterval = null;
    let mediaRunId = 0;
    let imageAdvanceTimer = null;

    const MEDIA_EXTENSIONS = ['mp4', 'webm', 'gif', 'png', 'jpg', 'jpeg'];

    function updateStatus(message, isError = false) {
        statusText.textContent = message;
        statusText.style.color = isError ? '#ef4444' : 'var(--text-muted)';
    }

    function escapeHtml(s) {
        const d = document.createElement('div');
        d.textContent = s == null ? '' : String(s);
        return d.innerHTML;
    }

    function resetSignMediaStage() {
        mediaRunId += 1;
        if (imageAdvanceTimer) {
            clearTimeout(imageAdvanceTimer);
            imageAdvanceTimer = null;
        }

        signPlayerVideo.pause();
        signPlayerVideo.removeAttribute('src');
        signPlayerVideo.load();
        signPlayerVideo.classList.add('hidden');

        signPlayerImage.removeAttribute('src');
        signPlayerImage.classList.add('hidden');

        signMediaLabel.textContent = '';
        signMediaLabel.classList.add('hidden');

        signMediaEmpty.textContent = 'No sign media found for this translation.';
        signMediaEmpty.classList.remove('hidden');
    }

    function uniqueTokenVariants(token) {
        const raw = (token || '').trim();
        if (!raw) {
            return [];
        }

        const normalized = raw
            .replace(/\s+/g, '_')
            .replace(/[^A-Za-z0-9_-]/g, '');
        const withDash = normalized.replace(/_/g, '-');

        const variants = [raw, normalized, withDash, raw.replace(/\s+/g, '-'), raw.replace(/\s+/g, '_')];
        const all = variants.flatMap((v) => [v, v.toLowerCase(), v.toUpperCase()]);

        return [...new Set(all.filter(Boolean))];
    }

    async function urlExists(url) {
        try {
            const resp = await fetch(url, { method: 'HEAD' });
            return resp.ok;
        } catch (_err) {
            return false;
        }
    }

    function tokenListFromSequence(sequence) {
        const tokens = [];
        (sequence || []).forEach((step) => {
            if (step.kind === 'lexical') {
                if (step.gloss) tokens.push(step.gloss);
                if (step.english) tokens.push(step.english);
            } else if (step.kind === 'fingerspell') {
                (step.letters || []).forEach((letter) => tokens.push(letter));
                if (step.english) tokens.push(step.english);
            } else if (step.text) {
                tokens.push(step.text);
            }
        });
        return tokens;
    }

    async function buildMediaPlaylist(sequence) {
        const tokens = tokenListFromSequence(sequence);
        const playlist = [];

        for (const token of tokens) {
            const variants = uniqueTokenVariants(token);
            let found = null;

            for (const name of variants) {
                for (const ext of MEDIA_EXTENSIONS) {
                    const url = `/static/signs/${encodeURIComponent(name)}.${ext}`;
                    // Resolve the first existing file for this token.
                    if (await urlExists(url)) {
                        found = {
                            url,
                            token,
                            type: ext === 'mp4' || ext === 'webm' ? 'video' : 'image',
                        };
                        break;
                    }
                }
                if (found) break;
            }

            if (found) {
                playlist.push(found);
            }
        }

        return playlist;
    }

    function showActiveSignLabel(token) {
        // Label display disabled - only show video
        signMediaLabel.classList.add('hidden');
    }

    function playMediaPlaylist(playlist, runId) {
        if (!playlist.length) {
            signMediaEmpty.textContent = 'No matching files in static/signs. Add files like hello.mp4 or hello.gif.';
            signMediaEmpty.classList.remove('hidden');
            signPlayerVideo.classList.add('hidden');
            signPlayerImage.classList.add('hidden');
            signMediaLabel.classList.add('hidden');
            return;
        }

        let index = 0;

        const playNext = () => {
            if (runId !== mediaRunId) {
                return;
            }

            const item = playlist[index % playlist.length];
            showActiveSignLabel(item.token);
            signMediaEmpty.classList.add('hidden');

            if (item.type === 'video') {
                signPlayerImage.classList.add('hidden');
                signPlayerImage.removeAttribute('src');

                signPlayerVideo.classList.remove('hidden');
                signPlayerVideo.src = item.url;
                signPlayerVideo.currentTime = 0;
                signPlayerVideo.onended = () => {
                    if (runId !== mediaRunId) return;
                    index += 1;
                    playNext();
                };
                signPlayerVideo.onerror = () => {
                    if (runId !== mediaRunId) return;
                    index += 1;
                    playNext();
                };

                signPlayerVideo.play().catch(() => {
                    index += 1;
                    playNext();
                });
            } else {
                signPlayerVideo.pause();
                signPlayerVideo.classList.add('hidden');

                signPlayerImage.classList.remove('hidden');
                signPlayerImage.src = item.url;

                imageAdvanceTimer = setTimeout(() => {
                    if (runId !== mediaRunId) return;
                    index += 1;
                    playNext();
                }, 1400);
            }
        };

        playNext();
    }

    async function renderSignOutput(data) {
        stopCamera();
        resetSignMediaStage();

        signPanel.classList.remove('hidden');
        signPlaceholder.classList.add('hidden');
        signOutput.classList.remove('hidden');

        signGlossLine.textContent = data.gloss_line || '';
        signGlossLine.classList.add('hidden');
        signSequence.innerHTML = '';
        signSequence.classList.add('hidden');

        const playlist = [];
        (data.sign_sequence || []).forEach((step) => {
            const el = document.createElement('div');
            el.className = 'sign-token';
            if (step.kind === 'lexical') {
                el.classList.add('lexical');
                el.innerHTML =
                    `<span class="sign-token-main">${escapeHtml(step.gloss)}</span>` +
                    `<span class="sign-token-sub">${escapeHtml(step.english || '')}</span>`;
                
                // Add to playlist if video URL is available
                if (step.video_url) {
                    playlist.push({
                        url: step.video_url,
                        token: step.gloss || step.english,
                        type: step.video_url.endsWith('.mp4') || step.video_url.endsWith('.webm') ? 'video' : 'image',
                    });
                }
            } else if (step.kind === 'fingerspell') {
                el.classList.add('fingerspell');
                const letters = (step.letters || []).join(' ');
                el.innerHTML =
                    `<span class="sign-token-main">${escapeHtml(letters)}</span>` +
                    `<span class="sign-token-sub">fingerspell: ${escapeHtml(step.english || '')}</span>`;
            } else {
                el.innerHTML = `<span class="sign-token-main">${escapeHtml(step.text || '')}</span>`;
            }
            signSequence.appendChild(el);
        });

        // Play the media playlist if any items have video URLs
        const currentRunId = mediaRunId;
        playMediaPlaylist(playlist, currentRunId);

        return playlist.length;
    }

    // --- 1. Text → Sign (backend gloss sequence) ---
    textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            translateTextBtn.click();
        }
    });

    translateTextBtn.addEventListener('click', async () => {
        const text = textInput.value.trim();
        if (!text) {
            updateStatus('Please enter text first.', true);
            return;
        }

        updateStatus('Translating text...');
        try {
            const resp = await fetch('/text-to-sign', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            const data = await resp.json();

            if (data.success) {
                const mediaCount = await renderSignOutput(data);
                if (mediaCount > 0) {
                    updateStatus(`${data.summary || 'Sign sequence generated'} Playing ${mediaCount} sign media item(s).`);
                } else {
                    updateStatus(data.summary || 'Sign sequence generated - no video files found');
                }
            } else {
                updateStatus(data.message || data.error || 'Translation failed.', true);
            }
        } catch (err) {
            console.error(err);
            updateStatus('Error connecting to server.', true);
        }
    });

    // --- 2. Voice → Text → Sign ---
    micBtn.addEventListener('click', () => {
        if (!isRecordingAudio) {
            startBrowserDictation();
        } else {
            stopBrowserDictation();
        }
    });

    function startBrowserDictation() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            updateStatus('Your browser does not support Speech Recognition.', true);
            return;
        }

        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            isRecordingAudio = true;
            micBtn.classList.add('recording');
            micBtn.querySelector('span').textContent = 'Stop';
            updateStatus('Listening...');
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            const currentText = textInput.value;
            textInput.value = (currentText ? currentText.trim() + ' ' : '') + transcript;
            updateStatus('Audio transcribed successfully');
            translateTextBtn.click();
        };

        recognition.onerror = (event) => {
            console.error(event.error);
            updateStatus('Microphone error.', true);
            stopBrowserDictation();
        };

        recognition.onend = () => {
            stopBrowserDictation();
        };

        try {
            recognition.start();
        } catch (e) {
            console.error(e);
        }
    }

    function stopBrowserDictation() {
        if (recognition) {
            recognition.stop();
        }
        isRecordingAudio = false;
        micBtn.classList.remove('recording');
        micBtn.querySelector('span').textContent = 'Speak';
        updateStatus('Processing audio...');
    }

    // --- 3. Text → Voice (browser TTS) ---
    speakerBtn.addEventListener('click', () => {
        const text = textInput.value.trim();
        if (!text) return;

        updateStatus('Playing audio...');
        speakerBtn.style.opacity = '0.7';

        const utterance = new SpeechSynthesisUtterance(text);

        utterance.onend = () => {
            updateStatus('Finished playing');
            speakerBtn.style.opacity = '1';
        };

        utterance.onerror = (e) => {
            console.error('Speech synthesis error', e);
            updateStatus('Error playing audio', true);
            speakerBtn.style.opacity = '1';
        };

        window.speechSynthesis.speak(utterance);
    });

    // --- 4. Camera → Text (optional: then user can press Play Audio) ---
    camBtn.addEventListener('click', () => {
        if (!isCameraActive) {
            startCamera();
        } else {
            stopCamera();
        }
    });

    async function startCamera() {
        try {
            webcamStream = await navigator.mediaDevices.getUserMedia({ video: true });
            webcamView.srcObject = webcamStream;

            signPanel.classList.add('hidden');
            cameraContainer.classList.remove('hidden');
            camBtn.classList.add('recording');
            camBtn.querySelector('span').textContent = 'Stop Cam';

            isCameraActive = true;
            updateStatus('Camera active. Analyzing gestures...');
            cameraInterval = setInterval(captureAndSendFrame, 1000);
        } catch (err) {
            console.error('Camera access denied', err);
            updateStatus('Camera access denied.', true);
        }
    }

    function stopCamera() {
        if (!isCameraActive) return;

        if (webcamStream) {
            webcamStream.getTracks().forEach((track) => track.stop());
        }
        clearInterval(cameraInterval);

        cameraContainer.classList.add('hidden');
        signPanel.classList.remove('hidden');
        camBtn.classList.remove('recording');
        camBtn.querySelector('span').textContent = 'Sign';

        isCameraActive = false;

        if (signGlossLine.textContent.trim()) {
            signPlaceholder.classList.add('hidden');
            signOutput.classList.remove('hidden');
        } else {
            signPlaceholder.classList.remove('hidden');
            signOutput.classList.add('hidden');
        }
        updateStatus('Camera stopped');
    }

    async function captureAndSendFrame() {
        if (!isCameraActive) return;

        const video = webcamView;
        if (!video.videoWidth || !video.videoHeight) {
            return;
        }

        const canvas = cameraCanvas;
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        const dataUrl = canvas.toDataURL('image/jpeg', 0.8);

        try {
            const resp = await fetch('/sign-to-text', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: dataUrl })
            });
            const data = await resp.json();

            if (data.success && data.text) {
                const currentText = textInput.value;
                const words = currentText.trim() ? currentText.trim().split(/\s+/) : [];
                const lastWord = words.length > 0 ? words[words.length - 1] : '';

                if (lastWord !== data.text) {
                    textInput.value = (currentText ? currentText.trim() + ' ' : '') + data.text;
                    updateStatus(`Detected sign: ${data.text}`);
                }
            }
        } catch (err) {
            console.error('Frame processing error', err);
        }
    }
});
