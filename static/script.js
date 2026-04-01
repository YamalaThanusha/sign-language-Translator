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
    let isSpeakingAudio = false;
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

    function mediaTypeFromUrl(url) {
        const clean = (url || '').split('?')[0].toLowerCase();
        return clean.endsWith('.mp4') || clean.endsWith('.webm') ? 'video' : 'image';
    }

    async function buildMediaPlaylist(sequence, alreadyUsedUrls = []) {
        const tokens = tokenListFromSequence(sequence);
        const playlist = [];
        const seen = new Set((alreadyUsedUrls || []).filter(Boolean));

        const mediaBases = ['/static/signs', '/static/signs/gifs', '/static/signs/videos'];

        for (const token of tokens) {
            const variants = uniqueTokenVariants(token);
            let found = null;

            for (const name of variants) {
                for (const base of mediaBases) {
                    for (const ext of MEDIA_EXTENSIONS) {
                        const url = `${base}/${encodeURIComponent(name)}.${ext}`;
                        if (seen.has(url)) {
                            continue;
                        }
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
                if (found) break;
            }

            if (found) {
                seen.add(found.url);
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
        const explicitMediaUrls = [];
        (data.sign_sequence || []).forEach((step) => {
            const el = document.createElement('div');
            el.className = 'sign-token';
            if (step.kind === 'lexical') {
                el.classList.add('lexical');
                el.innerHTML =
                    `<span class="sign-token-main">${escapeHtml(step.gloss)}</span>` +
                    `<span class="sign-token-sub">${escapeHtml(step.english || '')}</span>`;
                
                // Add to playlist if backend media URL is available.
                const backendUrl = step.video_url || step.gif_url || step.media_url;
                if (backendUrl) {
                    explicitMediaUrls.push(backendUrl);
                    playlist.push({
                        url: backendUrl,
                        token: step.gloss || step.english,
                        type: mediaTypeFromUrl(backendUrl),
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

        // Add fallback media discovery (GIF/image/video files in static folders)
        // for signs that did not provide explicit backend URLs.
        const discoveredPlaylist = await buildMediaPlaylist(data.sign_sequence || [], explicitMediaUrls);
        playlist.push(...discoveredPlaylist);

        // Play mixed media playlist (videos, GIFs, images).
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
        if (isSpeakingAudio) {
            updateStatus('Wait for audio playback to finish before recording.', true);
            return;
        }
        if (!isRecordingAudio) {
            startBrowserDictation();
        } else {
            stopBrowserDictation({ fromUser: true });
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
            // New dictation session should replace previous spoken text.
            textInput.value = '';
            updateStatus('Listening...');
        };

        recognition.onresult = (event) => {
            if (isSpeakingAudio) {
                return;
            }
            const transcript = event.results[0][0].transcript;
            textInput.value = transcript.trim();
            updateStatus('Audio transcribed successfully');
            translateTextBtn.click();
        };

        recognition.onerror = (event) => {
            console.error(event.error);
            updateStatus('Microphone error.', true);
            stopBrowserDictation({ fromError: true });
        };

        recognition.onend = () => {
            stopBrowserDictation({ fromRecognitionEnd: true });
        };

        try {
            recognition.start();
        } catch (e) {
            console.error(e);
        }
    }

    function stopBrowserDictation(opts = {}) {
        const wasRecording = isRecordingAudio;
        if (recognition && wasRecording && !opts.fromRecognitionEnd) {
            try {
                recognition.stop();
            } catch (_err) {
                // Some browsers throw if stop() is called while inactive.
            }
        }
        isRecordingAudio = false;
        micBtn.classList.remove('recording');
        micBtn.querySelector('span').textContent = 'Speak';

        if (opts.fromError) {
            return;
        }
        if (opts.fromUser) {
            updateStatus('Microphone stopped');
            return;
        }
        if (opts.fromRecognitionEnd && wasRecording) {
            updateStatus('Audio input complete');
        }
    }

    // --- 3. Text → Voice (browser TTS) ---
    speakerBtn.addEventListener('click', () => {
        const text = textInput.value.trim();
        if (!text) return;

        if (isRecordingAudio) {
            stopBrowserDictation({ fromUser: true });
        }

        if (window.speechSynthesis && window.speechSynthesis.speaking) {
            window.speechSynthesis.cancel();
        }

        updateStatus('Playing audio...');
        speakerBtn.style.opacity = '0.7';
        isSpeakingAudio = true;

        const utterance = new SpeechSynthesisUtterance(text);

        utterance.onend = () => {
            isSpeakingAudio = false;
            updateStatus('Finished playing');
            speakerBtn.style.opacity = '1';
        };

        utterance.onerror = (e) => {
            console.error('Speech synthesis error', e);
            isSpeakingAudio = false;
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
                textInput.value = data.text;
                updateStatus(`Detected sign: ${data.text}`);
                await playServerAudioFromText(data.text);
            } else if (data.success) {
                updateStatus('No sign detected yet. Hold your hand steady.', false);
            }
        } catch (err) {
            console.error('Frame processing error', err);
        }
    }

    async function playServerAudioFromText(text) {
        if (!text || !text.trim()) {
            return;
        }

        try {
            const resp = await fetch('/text-to-speech', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text.trim() })
            });
            const data = await resp.json();

            if (!resp.ok || !data.success || !data.audio_url) {
                return;
            }

            // Use backend-generated pyttsx3 audio output.
            const audio = new Audio(data.audio_url);
            await audio.play().catch(() => {
                // Ignore autoplay/browser policy failures silently.
            });
        } catch (_err) {
            // Keep sign recognition flow resilient if TTS endpoint fails.
        }
    }
});
