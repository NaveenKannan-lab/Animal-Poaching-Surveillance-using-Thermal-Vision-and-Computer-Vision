// State variables
let isRunning = false;
let startTime = null;
let timerInterval = null;
let pollInterval = null;
let lastAlertCount = 0;  // Track alert frames (human+animal)
let alertShown = false;
let currentFilename = 'video';

// Audio element for synced alerts
let alarmAudio = null;

// Settings
let settings = {
  confidence: 35,
  model: 'yolov8m.pt',
  soundEnabled: true,
  visualEnabled: true,
  autoSave: true,
  maxFrames: 100
};

// Detection history
let detectionHistory = JSON.parse(localStorage.getItem('detectionHistory') || '[]');

// DOM Elements
const uploadZone = document.getElementById('uploadZone');
const videoInput = document.getElementById('videoInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const uploadBtn = document.getElementById('uploadBtn');
const startBtn = document.getElementById('startBtn');
const videoOverlay = document.getElementById('videoOverlay');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const detectionBadge = document.getElementById('detectionBadge');
const alertModal = document.getElementById('alertModal');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  updateTime();
  setInterval(updateTime, 1000);
  setupUploadZone();
  loadSettings();
  renderHistory();
  
  // Initialize alarm audio
  alarmAudio = new Audio('/static/audio/alarm.mp3');
  alarmAudio.preload = 'auto';
});

// Update current time
function updateTime() {
  const now = new Date();
  document.getElementById('currentTime').textContent = now.toLocaleString();
}

// Setup upload zone drag & drop
function setupUploadZone() {
  uploadZone.addEventListener('click', () => videoInput.click());
  
  uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
  });
  
  uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
  });
  
  uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('video/')) {
      handleFileSelect(file);
    }
  });
  
  videoInput.addEventListener('change', (e) => {
    if (e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  });
}

// Handle file selection
function handleFileSelect(file) {
  fileName.textContent = file.name;
  uploadZone.style.display = 'none';
  fileInfo.style.display = 'flex';
  uploadBtn.disabled = false;
}

// Remove selected file
function removeFile() {
  videoInput.value = '';
  uploadZone.style.display = 'block';
  fileInfo.style.display = 'none';
  uploadBtn.disabled = true;
  startBtn.disabled = true;
}

// Upload video
async function upload() {
  const file = videoInput.files[0];
  if (!file) return;
  
  uploadBtn.disabled = true;
  uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
  
  const formData = new FormData();
  formData.append('video', file);
  
  try {
    const res = await fetch('/upload', { method: 'POST', body: formData });
    const data = await res.json();
    
    if (data.status === 'uploaded') {
      currentFilename = data.filename || 'video';
      uploadBtn.innerHTML = '<i class="fas fa-check"></i> Uploaded';
      uploadBtn.classList.remove('btn-primary');
      uploadBtn.classList.add('btn-success');
      startBtn.disabled = false;
      showNotification('Video uploaded successfully!', 'success');
    }
  } catch (err) {
    uploadBtn.innerHTML = '<i class="fas fa-upload"></i> Upload Video';
    uploadBtn.disabled = false;
    showNotification('Upload failed. Please try again.', 'error');
  }
}

// Start detection
async function start() {
  if (isRunning) return;
  
  startBtn.disabled = true;
  startBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
  
  try {
    await fetch('/start', { method: 'POST' });
    
    isRunning = true;
    startBtn.innerHTML = '<i class="fas fa-stop"></i> Running...';
    videoOverlay.classList.add('hidden');
    
    // Update status
    statusDot.classList.add('active');
    statusText.textContent = 'Monitoring';
    
    // Start timer
    startTime = Date.now();
    timerInterval = setInterval(updateTimer, 1000);
    
    // Start polling for detections
    pollInterval = setInterval(pollDetections, 1000);
    
    showNotification('Detection started!', 'success');
  } catch (err) {
    startBtn.innerHTML = '<i class="fas fa-play"></i> Start Detection';
    startBtn.disabled = false;
    showNotification('Failed to start detection.', 'error');
  }
}

// Update timer
function updateTimer() {
  if (!startTime) return;
  const elapsed = Math.floor((Date.now() - startTime) / 1000);
  const mins = Math.floor(elapsed / 60).toString().padStart(2, '0');
  const secs = (elapsed % 60).toString().padStart(2, '0');
  document.getElementById('runTime').textContent = `${mins}:${secs}`;
}

// Poll for detections - alerts only when BOTH human AND animal detected
async function pollDetections() {
  try {
    const res = await fetch('/humans');
    const data = await res.json();
    
    // Update counts
    const humanCount = data.humans || 0;
    const animalCount = data.animals || 0;
    const alertCount = data.alerts || 0;  // Poaching alerts (human+animal)
    const frames = data.frames || [];
    
    document.getElementById('humanCount').textContent = humanCount;
    document.getElementById('animalCount').textContent = animalCount;
    document.getElementById('alertCount').textContent = alertCount;
    document.getElementById('frameCount').textContent = `${frames.length} frames`;
    
    // Enable/disable export button based on alert frames
    const exportBtn = document.getElementById('exportBtn');
    if (frames.length > 0) {
      exportBtn.disabled = false;
    } else {
      exportBtn.disabled = true;
    }
    
    // Check if video completed
    if (data.completed && isRunning) {
      handleVideoComplete(data);
      return;
    }
    
    // SYNCED ALERT: Sound + Visual together when backend signals alert_pending
    // Alert only triggers when BOTH human AND animal detected in same frame
    if (data.alert_pending) {
      // Play sound (synced with detection)
      if (settings.soundEnabled && alarmAudio) {
        alarmAudio.currentTime = 0;
        alarmAudio.play().catch(e => console.log('Audio play blocked:', e));
      }
      
      // Show visual alert
      statusDot.classList.add('alert');
      detectionBadge.innerHTML = '<span class="badge badge-danger">⚠ POACHING ALERT!</span>';
      
      if (!alertShown && settings.visualEnabled) {
        alertModal.classList.add('show');
        alertShown = true;
      }
    }
    
    // Add new alert frames to timeline
    if (frames.length > lastAlertCount) {
      for (let i = lastAlertCount; i < frames.length; i++) {
        addTimelineEntry(frames[i], i);
      }
    }
    
    // Update status if no alerts
    if (alertCount === 0) {
      statusDot.classList.remove('alert');
      detectionBadge.innerHTML = '<span class="badge badge-success">No Threat</span>';
    }
    
    lastAlertCount = frames.length;
    
    // Update gallery
    updateGallery(frames);
    
  } catch (err) {
    console.error('Polling error:', err);
  }
}

// Handle video completion
function handleVideoComplete(data) {
  // Stop polling and timer
  clearInterval(pollInterval);
  clearInterval(timerInterval);
  isRunning = false;
  
  // Update UI
  statusDot.classList.remove('active');
  statusDot.classList.remove('alert');
  statusText.textContent = 'Completed';
  startBtn.innerHTML = '<i class="fas fa-check-circle"></i> Completed';
  detectionBadge.innerHTML = '<span class="badge badge-success">Detection Complete</span>';
  
  // Save to history
  if (settings.autoSave) {
    saveToHistory(
      data.filename || currentFilename,
      data.humans,
      data.animals,
      data.duration,
      data.thumbnail
    );
  }
  
  // Show completion message
  showCompletionModal(data);
}

// Show completion modal
function showCompletionModal(data) {
  const alertContent = document.querySelector('.alert-content');
  alertContent.innerHTML = `
    <i class="fas fa-check-circle" style="color: var(--accent-green)"></i>
    <h2 style="color: var(--accent-green)">Detection Complete!</h2>
    <p>Video analysis finished successfully.</p>
    <div class="completion-stats">
      <div class="completion-stat">
        <span class="stat-value" style="color: var(--accent-red)">${data.humans}</span>
        <span class="stat-label">Humans Detected</span>
      </div>
      <div class="completion-stat">
        <span class="stat-value" style="color: var(--accent-green)">${data.animals}</span>
        <span class="stat-label">Animals Detected</span>
      </div>
      <div class="completion-stat">
        <span class="stat-value" style="color: var(--accent-blue)">${data.duration}</span>
        <span class="stat-label">Duration</span>
      </div>
    </div>
    <button class="btn btn-success" onclick="dismissAlert(); resetForNewVideo();">
      <i class="fas fa-redo"></i> Analyze Another Video
    </button>
  `;
  alertModal.classList.add('show');
}

// Reset for new video
function resetForNewVideo() {
  // Reset state
  lastAlertCount = 0;
  alertShown = false;
  startTime = null;
  
  // Reset UI
  uploadZone.style.display = 'block';
  fileInfo.style.display = 'none';
  uploadBtn.disabled = true;
  uploadBtn.innerHTML = '<i class="fas fa-upload"></i> Upload Video';
  uploadBtn.classList.remove('btn-success');
  uploadBtn.classList.add('btn-primary');
  startBtn.disabled = true;
  startBtn.innerHTML = '<i class="fas fa-play"></i> Start Detection';
  videoOverlay.classList.remove('hidden');
  statusText.textContent = 'Idle';
  
  // Reset counters
  document.getElementById('humanCount').textContent = '0';
  document.getElementById('animalCount').textContent = '0';
  document.getElementById('alertCount').textContent = '0';
  document.getElementById('runTime').textContent = '00:00';
  document.getElementById('frameCount').textContent = '0 frames';
  
  // Disable export button
  document.getElementById('exportBtn').disabled = true;
  
  // Clear timeline and gallery
  clearTimeline();
  document.getElementById('gallery').innerHTML = `
    <div class="gallery-empty">
      <i class="fas fa-camera"></i>
      <p>Poaching alert frames will appear here</p>
    </div>
  `;
  
  // Reset alert content
  document.querySelector('.alert-content').innerHTML = `
    <i class="fas fa-exclamation-triangle"></i>
    <h2>POACHING ALERT!</h2>
    <p>Human detected near wildlife - potential poaching activity!</p>
    <button class="btn btn-danger" onclick="dismissAlert()">Dismiss Alert</button>
  `;
}

// Add entry to timeline
function addTimelineEntry(detection, index) {
  const timeline = document.getElementById('timeline');
  const empty = timeline.querySelector('.timeline-empty');
  if (empty) empty.remove();
  
  const now = new Date();
  const timeStr = now.toLocaleTimeString();
  
  // Calculate approximate video timestamp based on detection order
  const videoTime = formatVideoTime(index);
  
  const entry = document.createElement('div');
  entry.className = 'timeline-item';
  entry.innerHTML = `
    <div class="timeline-icon">
      <i class="fas fa-user"></i>
    </div>
    <div class="timeline-info">
      <div class="timeline-title">Poaching Alert #${index + 1}</div>
      <div class="timeline-time">${timeStr}</div>
    </div>
    <div class="timeline-timestamp">
      <i class="fas fa-film"></i> ${videoTime}
    </div>
  `;
  
  timeline.insertBefore(entry, timeline.firstChild);
}

// Format video timestamp
function formatVideoTime(frameIndex) {
  // Approximate: assuming 30fps and detection every ~0.5 seconds
  const seconds = Math.floor(frameIndex * 0.5);
  const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
  const secs = (seconds % 60).toString().padStart(2, '0');
  return `${mins}:${secs}`;
}

// Update gallery
function updateGallery(detections) {
  const gallery = document.getElementById('gallery');
  const empty = gallery.querySelector('.gallery-empty');
  if (empty && detections.length > 0) empty.remove();
  
  // Clear and rebuild gallery
  if (detections.length > 0) {
    gallery.innerHTML = '';
    detections.forEach((imgData, index) => {
      const timestamp = formatVideoTime(index);
      
      const item = document.createElement('div');
      item.className = 'gallery-item';
      item.innerHTML = `
        <img src="data:image/jpeg;base64,${imgData}" alt="Detection ${index + 1}">
        <div class="gallery-item-info">
          <i class="fas fa-clock"></i> ${timestamp}
        </div>
      `;
      gallery.appendChild(item);
    });
  }
}

// Clear timeline
function clearTimeline() {
  const timeline = document.getElementById('timeline');
  timeline.innerHTML = `
    <div class="timeline-empty">
      <i class="fas fa-hourglass-start"></i>
      <p>No detections yet. Start monitoring to see timeline.</p>
    </div>
  `;
}

// Dismiss alert
function dismissAlert() {
  alertModal.classList.remove('show');
  setTimeout(() => { alertShown = false; }, 5000);
}

// Show notification
function showNotification(message, type) {
  console.log(`[${type.toUpperCase()}] ${message}`);
}

// ============ PAGE NAVIGATION ============

function showPage(page) {
  // Hide all pages
  document.getElementById('livePage').style.display = 'none';
  document.getElementById('historyPage').style.display = 'none';
  document.getElementById('settingsPage').style.display = 'none';
  
  // Remove active class from all nav items
  document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
  
  // Show selected page and activate nav item
  if (page === 'live') {
    document.getElementById('livePage').style.display = 'grid';
    document.querySelectorAll('.nav-item')[0].classList.add('active');
  } else if (page === 'history') {
    document.getElementById('historyPage').style.display = 'block';
    document.querySelectorAll('.nav-item')[1].classList.add('active');
    renderHistory();
  } else if (page === 'settings') {
    document.getElementById('settingsPage').style.display = 'block';
    document.querySelectorAll('.nav-item')[2].classList.add('active');
  }
}

// ============ HISTORY FUNCTIONS ============

function renderHistory() {
  const historyList = document.getElementById('historyList');
  
  if (detectionHistory.length === 0) {
    historyList.innerHTML = `
      <div class="history-empty">
        <i class="fas fa-folder-open"></i>
        <p>No detection history yet. Complete a detection session to see records here.</p>
      </div>
    `;
    return;
  }
  
  historyList.innerHTML = detectionHistory.map((session, index) => `
    <div class="history-item">
      <img src="data:image/jpeg;base64,${session.thumbnail || ''}" class="history-thumb" alt="Session ${index + 1}" 
           onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22120%22 height=%2270%22><rect fill=%22%231a2234%22 width=%22120%22 height=%2270%22/><text x=%2260%22 y=%2240%22 fill=%22%2394a3b8%22 text-anchor=%22middle%22 font-size=%2212%22>No Image</text></svg>'">
      <div class="history-info">
        <div class="history-title">${session.filename || 'Detection Session'}</div>
        <div class="history-meta">
          <span><i class="fas fa-calendar"></i> ${session.date}</span>
          <span><i class="fas fa-clock"></i> ${session.duration}</span>
        </div>
      </div>
      <div class="history-stats">
        <div class="history-stat">
          <div class="history-stat-value">${session.humans}</div>
          <div class="history-stat-label">Humans</div>
        </div>
        <div class="history-stat">
          <div class="history-stat-value" style="color: var(--accent-green)">${session.animals}</div>
          <div class="history-stat-label">Animals</div>
        </div>
      </div>
    </div>
  `).join('');
}

function saveToHistory(filename, humans, animals, duration, thumbnail) {
  const session = {
    filename: filename,
    date: new Date().toLocaleDateString(),
    duration: duration,
    humans: humans,
    animals: animals,
    thumbnail: thumbnail
  };
  
  detectionHistory.unshift(session);
  if (detectionHistory.length > 20) detectionHistory.pop(); // Keep last 20 sessions
  localStorage.setItem('detectionHistory', JSON.stringify(detectionHistory));
}

function clearHistory() {
  if (confirm('Are you sure you want to clear all detection history?')) {
    detectionHistory = [];
    localStorage.removeItem('detectionHistory');
    renderHistory();
  }
}

function exportHistory() {
  const data = JSON.stringify(detectionHistory, null, 2);
  const blob = new Blob([data], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `detection-history-${new Date().toISOString().split('T')[0]}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

// ============ SETTINGS FUNCTIONS ============

function loadSettings() {
  const saved = localStorage.getItem('detectionSettings');
  if (saved) {
    settings = JSON.parse(saved);
  }
  
  // Apply to UI
  document.getElementById('confidenceSlider').value = settings.confidence;
  document.getElementById('confidenceValue').textContent = settings.confidence + '%';
  document.getElementById('modelSelect').value = settings.model;
  document.getElementById('soundToggle').checked = settings.soundEnabled;
  document.getElementById('visualToggle').checked = settings.visualEnabled;
  document.getElementById('autoSaveToggle').checked = settings.autoSave;
  document.getElementById('maxFramesSelect').value = settings.maxFrames;
}

function updateConfidence(value) {
  document.getElementById('confidenceValue').textContent = value + '%';
  settings.confidence = parseInt(value);
}

function updateModel(value) {
  settings.model = value;
}

function updateSound(checked) {
  settings.soundEnabled = checked;
}

function updateVisual(checked) {
  settings.visualEnabled = checked;
}

function saveSettings() {
  settings.autoSave = document.getElementById('autoSaveToggle').checked;
  settings.maxFrames = parseInt(document.getElementById('maxFramesSelect').value);
  
  localStorage.setItem('detectionSettings', JSON.stringify(settings));
  
  // Send to backend
  fetch('/settings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings)
  }).then(() => {
    showNotification('Settings saved successfully!', 'success');
    alert('Settings saved! Restart detection to apply changes.');
  }).catch(() => {
    // Still save locally even if backend fails
    alert('Settings saved locally!');
  });
}

function resetSettings() {
  if (confirm('Reset all settings to default?')) {
    settings = {
      confidence: 35,
      model: 'yolov8m.pt',
      soundEnabled: true,
      visualEnabled: true,
      autoSave: true,
      maxFrames: 100
    };
    localStorage.setItem('detectionSettings', JSON.stringify(settings));
    loadSettings();
    alert('Settings reset to default!');
  }
}

// Export alert frames as zip
function exportAlertFrames() {
  const exportBtn = document.getElementById('exportBtn');
  const originalText = exportBtn.innerHTML;
  
  exportBtn.disabled = true;
  exportBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exporting...';
  
  fetch('/export')
    .then(response => {
      if (!response.ok) {
        if (response.status === 400) {
          showNotification('No alert frames to export!', 'warning');
        } else {
          throw new Error('Export failed');
        }
      } else {
        return response.blob().then(blob => {
          // Create download link
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `alert_frames_${new Date().toISOString().slice(0, 10)}.zip`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
          showNotification('Alert frames exported successfully!', 'success');
        });
      }
    })
    .catch(error => {
      console.error('Error exporting frames:', error);
      showNotification('Error exporting frames!', 'error');
    })
    .finally(() => {
      exportBtn.disabled = false;
      exportBtn.innerHTML = originalText;
    });
}