/**
 * AMT-8000 Alarm Manager - Frontend Controller
 * Implements real-time polling, state management, search/filter,
 * and responsive UI updates with beautiful micro-animations.
 */

// State Management
const state = {
    data: null,
    config: null,
    activeFilter: 'all',
    searchQuery: '',
    isPolling: false,
    pollTimer: null,
    actionPending: false,
};

// Selectors
const elements = {
    ingressPathMeta: document.querySelector('meta[name="ingress-path"]'),
    loadingOverlay: document.getElementById('loading-overlay'),
    errorContainer: document.getElementById('error-container'),
    errorMessage: document.getElementById('error-message'),
    btnRetry: document.getElementById('btn-retry'),
    dashboardUi: document.getElementById('dashboard-ui'),
    
    // Header
    firmwareBadge: document.getElementById('firmware-badge'),
    connectionBadge: document.getElementById('connection-badge'),
    connectionDot: document.getElementById('connection-dot'),
    connectionText: document.getElementById('connection-text'),
    
    // Overview
    valSystemStatus: document.getElementById('val-system-status'),
    cardSystemStatus: document.getElementById('card-system-status'),
    valArmedPartitions: document.getElementById('val-armed-partitions'),
    valViolatedZones: document.getElementById('val-violated-zones'),
    valBypassedZones: document.getElementById('val-bypassed-zones'),
    
    // Grids & Sections
    partitionsGrid: document.getElementById('partitions-grid'),
    partitionsCount: document.getElementById('partitions-count'),
    zonesGrid: document.getElementById('zones-grid'),
    zonesCount: document.getElementById('zones-count'),
    zoneSearch: document.getElementById('zone-search'),
    
    // Diagnostics
    sysIp: document.getElementById('sys-ip'),
    sysPort: document.getElementById('sys-port'),
    sysBattery: document.getElementById('sys-battery'),
    sysUpdate: document.getElementById('sys-update'),
    
    // Modal
    modalOverlay: document.getElementById('modal-overlay'),
    modalTitle: document.getElementById('modal-title'),
    modalMessage: document.getElementById('modal-message'),
    modalConfirmBtn: document.getElementById('modal-confirm-btn'),
    
    // Toast
    toastContainer: document.getElementById('toast-container'),
};

// Ingress Prefix
const INGRESS_PATH = elements.ingressPathMeta ? elements.ingressPathMeta.getAttribute('content') : '';

// ============================================================================
// Core Polling and API Service
// ============================================================================

/**
 * Fetch non-sensitive configuration parameters
 */
async function fetchConfig() {
    try {
        const response = await fetch(`${INGRESS_PATH}/api/config`);
        if (response.ok) {
            state.config = await response.json();
            elements.sysIp.textContent = state.config.host || 'Desconhecido';
            elements.sysPort.textContent = state.config.port || '9009';
        }
    } catch (err) {
        console.error('Error fetching config:', err);
    }
}

/**
 * Perform connection status and state polling
 */
async function pollStatus(isFirstLoad = false) {
    if (state.actionPending) return; // Wait during active command transitions

    try {
        const response = await fetch(`${INGRESS_PATH}/api/status`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const res = await response.json();
        
        if (res.success && res.connected) {
            state.data = res.data;
            showDashboard();
            updateUI(res.lastUpdate, res.error);
        } else {
            // Panel has server running but cannot connect to physical AMT-8000 central
            showError(res.error || 'A central de alarme está desconectada ou inacessível.');
        }
    } catch (err) {
        console.error('Polling error:', err);
        if (isFirstLoad) {
            showError('Não foi possível conectar ao servidor do Add-on. Verifique se o Add-on foi iniciado.');
        } else {
            // Keep showing dashboard but mark offline
            markHeaderOffline('Erro de Servidor');
        }
    }
}

/**
 * Initialize polling intervals based on config
 */
function startPolling() {
    if (state.isPolling) return;
    state.isPolling = true;
    
    const interval = state.config ? (state.config.updateInterval * 1000) : 4000;
    
    state.pollTimer = setInterval(() => pollStatus(false), interval);
}

function stopPolling() {
    if (state.pollTimer) {
        clearInterval(state.pollTimer);
        state.pollTimer = null;
    }
    state.isPolling = false;
}

// ============================================================================
// UI Controllers and Transitions
// ============================================================================

function showDashboard() {
    elements.loadingOverlay.style.display = 'none';
    elements.errorContainer.style.display = 'none';
    elements.dashboardUi.style.display = 'block';
}

function showError(message) {
    elements.loadingOverlay.style.display = 'none';
    elements.dashboardUi.style.display = 'none';
    elements.errorContainer.style.display = 'flex';
    elements.errorMessage.textContent = message;
}

function markHeaderOffline(reason = 'Desconectado') {
    elements.connectionBadge.className = 'connection-badge offline';
    elements.connectionDot.className = 'connection-dot offline';
    elements.connectionText.textContent = reason;
}

function updateUI(timestamp, errorMsg) {
    if (!state.data) return;

    // 1. Connection & Header Badge
    if (errorMsg) {
        markHeaderOffline(errorMsg);
    } else {
        elements.connectionBadge.className = 'connection-badge online';
        elements.connectionDot.className = 'connection-dot online';
        elements.connectionText.textContent = 'Conectado';
    }
    
    elements.firmwareBadge.textContent = `V ${state.data.version || '--'}`;

    // 2. Overview Counts & Status Card
    const sysStatus = state.data.status || 'unknown';
    let statusText = 'Desconhecido';
    let statusClass = 'status-info';
    
    if (sysStatus === 'armed_away') {
        statusText = 'Armado Total';
        statusClass = 'status-armed';
    } else if (sysStatus === 'partial_armed') {
        statusText = 'Armado Parcial';
        statusClass = 'status-bypassed';
    } else if (sysStatus === 'disarmed') {
        statusText = 'Desarmado';
        statusClass = 'status-disarmed';
    }
    
    if (state.data.siren || state.data.zonesFiring) {
        statusText = 'DISPARADO!';
        statusClass = 'status-danger';
    }

    elements.valSystemStatus.textContent = statusText;
    elements.cardSystemStatus.className = `overview-card ${statusClass}`;

    // Count statistics
    const partitions = Object.values(state.data.partitions || {});
    const enabledPartitions = partitions.filter(p => p.enabled);
    const armedPartCount = enabledPartitions.filter(p => p.armed).length;
    elements.valArmedPartitions.textContent = armedPartCount;

    const zones = Object.values(state.data.zones || {});
    const enabledZones = zones.filter(z => z.enabled);
    const violatedZoneCount = enabledZones.filter(z => z.open || z.violated).length;
    elements.valViolatedZones.textContent = violatedZoneCount;

    const bypassedZoneCount = enabledZones.filter(z => z.bypassed).length;
    elements.valBypassedZones.textContent = bypassedZoneCount;

    // 3. Render Grid Panels
    renderPartitions(enabledPartitions);
    renderZones(enabledZones);

    // 4. Diagnostic Indicators
    const battStatus = state.data.batteryStatus || 'unknown';
    const battPercent = state.data.batteryPercentage || 0;
    
    // Map battery
    let battIcon = 'fa-battery-full';
    let battColor = '#22c55e';
    if (battStatus === 'medium') { battIcon = 'fa-battery-three-quarters'; battColor = '#f59e0b'; }
    else if (battStatus === 'low') { battIcon = 'fa-battery-quarter'; battColor = '#ef4444'; }
    else if (battStatus === 'dead') { battIcon = 'fa-battery-empty'; battColor = '#ef4444'; }

    elements.sysBattery.innerHTML = `
        <span class="battery-indicator" style="color: ${battColor};">
            <i class="fa-solid ${battIcon}"></i> ${battPercent}% (${translateBattery(battStatus)})
        </span>
    `;

    // Last Update Time
    const date = new Date(timestamp * 1000);
    elements.sysUpdate.textContent = date.toLocaleTimeString('pt-BR');
}

function translateBattery(status) {
    const translation = {
        'full': 'Cheia',
        'medium': 'Média',
        'low': 'Fraca',
        'dead': 'Crítica',
        'unknown': '--'
    };
    return translation[status] || status;
}

// ============================================================================
// Renderers
// ============================================================================

/**
 * Render active partitions list
 */
function renderPartitions(partitions) {
    elements.partitionsCount.textContent = partitions.length;
    
    if (partitions.length === 0) {
        elements.partitionsGrid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: var(--spacing-xl);">
                Nenhuma partição configurada ou ativa na central.
            </div>
        `;
        return;
    }

    elements.partitionsGrid.innerHTML = partitions.map(p => {
        let statusClass = 'disarmed';
        let statusIndicatorClass = 'disarmed';
        let statusText = 'Desarmada';
        
        if (p.firing || p.fired) {
            statusClass = 'firing';
            statusIndicatorClass = 'firing';
            statusText = 'Disparada';
        } else if (p.armed) {
            statusClass = 'armed';
            statusIndicatorClass = 'armed';
            statusText = p.stay ? 'Armado Parcial' : 'Armado Total';
        }

        const isArmed = p.armed;
        const armBtnLabel = 'Armar';
        const disarmBtnLabel = 'Desarmar';

        return `
            <div class="partition-card" id="partition-${p.number}">
                <div class="partition-header">
                    <span class="partition-name">Partição ${p.number.toString().padStart(2, '0')}</span>
                    <span class="partition-status-indicator ${statusIndicatorClass}"></span>
                </div>
                
                <div class="partition-status">
                    <span class="partition-status-text ${statusClass}">${statusText}</span>
                </div>

                <div class="partition-badges">
                    ${p.stay ? '<span class="mini-badge stay">STAY</span>' : ''}
                    ${p.fired ? '<span class="mini-badge fired">DISPARADO</span>' : ''}
                </div>

                <div class="partition-actions">
                    ${isArmed ? 
                        `<button class="btn btn-disarm btn-sm" onclick="handlePartitionAction(${p.number}, 'disarm', this)">
                            <i class="fa-solid fa-lock-open"></i> ${disarmBtnLabel}
                         </button>` : 
                        `<button class="btn btn-arm btn-sm" onclick="handlePartitionAction(${p.number}, 'arm', this)">
                            <i class="fa-solid fa-lock"></i> ${armBtnLabel}
                         </button>`
                    }
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Render enabled zones
 */
function renderZones(zones) {
    const filtered = zones.filter(z => {
        // Filter by Query
        const matchSearch = z.number.toString().includes(state.searchQuery) || 
                            `zona ${z.number}`.includes(state.searchQuery.toLowerCase());
        
        if (!matchSearch) return false;

        // Filter by Mode
        if (state.activeFilter === 'all') return true;
        if (state.activeFilter === 'open') return z.open || z.violated;
        if (state.activeFilter === 'bypassed') return z.bypassed;
        if (state.activeFilter === 'closed') return !z.open && !z.violated;
        return true;
    });

    elements.zonesCount.textContent = `${filtered.length} de ${zones.length}`;

    if (filtered.length === 0) {
        elements.zonesGrid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: var(--spacing-xl);">
                Nenhuma zona encontrada para os filtros aplicados.
            </div>
        `;
        return;
    }

    elements.zonesGrid.innerHTML = filtered.map(z => {
        let cardStateClass = 'closed';
        if (z.bypassed) cardStateClass = 'bypassed';
        else if (z.open) cardStateClass = 'open';
        else if (z.violated) cardStateClass = 'violated';

        return `
            <div class="zone-card ${cardStateClass}" id="zone-${z.number}">
                <div class="zone-number">${z.number.toString().padStart(2, '0')}</div>
                
                <div class="zone-info">
                    <div class="zone-name">Zona ${z.number.toString().padStart(2, '0')}</div>
                    
                    <div class="zone-telemetry">
                        <span class="zone-telemetry-item" title="${z.tamper ? 'Problema de Sinal ou Sensor Violado/Tamper' : 'Sinal sem fio OK'}">
                            <i class="fa-solid fa-signal" style="color: ${z.tamper ? 'var(--color-danger)' : 'var(--color-armed)'};"></i>
                            <span class="telemetry-text" style="color: ${z.tamper ? 'var(--color-danger)' : 'var(--text-secondary)'};">${z.tamper ? 'Sinal Ruim' : 'Sinal OK'}</span>
                        </span>
                        <span class="zone-telemetry-item" title="${z.lowBattery ? 'Bateria Fraca - Substitua a bateria' : 'Bateria OK'}">
                            <i class="fa-solid ${z.lowBattery ? 'fa-battery-quarter' : 'fa-battery-full'}" style="color: ${z.lowBattery ? 'var(--color-danger)' : 'var(--color-armed)'}; ${z.lowBattery ? 'animation: pulse-danger 1.5s infinite;' : ''}"></i>
                            <span class="telemetry-text" style="color: ${z.lowBattery ? 'var(--color-danger)' : 'var(--text-secondary)'};">${z.lowBattery ? 'Bat. Fraca' : 'Bat. OK'}</span>
                        </span>
                    </div>

                    <div class="zone-status-badges" style="margin-top: 6px;">
                        ${z.open ? '<span class="zone-badge open">Aberta</span>' : '<span class="zone-badge closed">Fechada</span>'}
                        ${z.violated ? '<span class="zone-badge violated">Violada</span>' : ''}
                        ${z.bypassed ? '<span class="zone-badge bypassed">Anulada</span>' : ''}
                        ${z.tamper ? '<span class="zone-badge tamper">Tamper</span>' : ''}
                        ${z.lowBattery ? '<span class="zone-badge low-battery"><i class="fa-solid fa-battery-quarter"></i> Bateria Baixa</span>' : ''}
                    </div>
                </div>

                <div class="zone-actions">
                    <label class="toggle-switch" title="Anular (Bypass) Zona">
                        <input type="checkbox" ${z.bypassed ? 'checked' : ''} onchange="handleBypassToggle(${z.number}, this)">
                        <span class="toggle-slider"></span>
                    </label>
                </div>
            </div>
        `;
    }).join('');
}

// ============================================================================
// Actions & API Call Handlers
// ============================================================================

/**
 * Handle partition arm/disarm triggers
 */
async function handlePartitionAction(partitionId, action, button) {
    if (state.actionPending) return;
    
    const originalContent = button.innerHTML;
    button.disabled = true;
    button.innerHTML = `<span class="spinner"></span> Processando...`;
    
    state.actionPending = true;
    stopPolling();

    try {
        const url = `${INGRESS_PATH}/api/partition/${partitionId}/${action}`;
        const response = await fetch(url, { method: 'POST' });
        const res = await response.json();

        if (res.success) {
            showToast(`Partição ${partitionId} ${action === 'arm' ? 'armada' : 'desarmada'} com sucesso!`, 'success');
        } else {
            showToast(`Falha ao operar partição: ${res.error || 'Erro desconhecido'}`, 'error');
        }
    } catch (err) {
        console.error(err);
        showToast('Erro de comunicação com o servidor.', 'error');
    } finally {
        button.innerHTML = originalContent;
        button.disabled = false;
        state.actionPending = false;
        
        // Immediate status refresh and restart polling
        await pollStatus(false);
        startPolling();
    }
}

/**
 * Handle bypass/unbypass zone toggles
 */
async function handleBypassToggle(zoneId, checkbox) {
    const shouldBypass = checkbox.checked;
    checkbox.disabled = true;
    
    state.actionPending = true;
    stopPolling();

    try {
        const action = shouldBypass ? 'bypass' : 'unbypass';
        const url = `${INGRESS_PATH}/api/zone/${zoneId}/${action}`;
        const response = await fetch(url, { method: 'POST' });
        const res = await response.json();

        if (res.success) {
            showToast(`Zona ${zoneId} ${shouldBypass ? 'anulada (bypass)' : 'reativada'}!`, 'success');
        } else {
            showToast(`Falha ao alterar estado da zona: ${res.error || 'Erro desconhecido'}`, 'error');
            // Revert state
            checkbox.checked = !shouldBypass;
        }
    } catch (err) {
        console.error(err);
        showToast('Erro de comunicação.', 'error');
        checkbox.checked = !shouldBypass;
    } finally {
        checkbox.disabled = false;
        state.actionPending = false;
        
        await pollStatus(false);
        startPolling();
    }
}

/**
 * Handle global quick actions (arm all, disarm all)
 */
async function executeGlobalAction(action) {
    closeModal();
    state.actionPending = true;
    stopPolling();
    
    showToast('Processando comando global...', 'info');

    try {
        let url = '';
        let successMessage = '';
        
        if (action === 'arm_all') {
            url = `${INGRESS_PATH}/api/partition/all/arm`;
            successMessage = 'Todas as partições foram armadas!';
        } else if (action === 'disarm_all') {
            url = `${INGRESS_PATH}/api/partition/all/disarm`;
            successMessage = 'Todas as partições foram desarmadas!';
        }

        const response = await fetch(url, { method: 'POST' });
        const res = await response.json();

        if (res.success) {
            showToast(successMessage, 'success');
        } else {
            showToast(`Falha no comando global: ${res.error || 'Erro desconhecido'}`, 'error');
        }
    } catch (err) {
        console.error(err);
        showToast('Erro de conexão.', 'error');
    } finally {
        state.actionPending = false;
        await pollStatus(false);
        startPolling();
    }
}

/**
 * Trigger panic alarms
 */
async function executePanic(type) {
    closeModal();
    state.actionPending = true;
    stopPolling();

    showToast('Acionando pânico!', 'warning');

    try {
        const response = await fetch(`${INGRESS_PATH}/api/panic`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: type })
        });
        const res = await response.json();

        if (res.success) {
            showToast(`Pânico ${type === 1 ? 'Sonoro' : 'Silencioso'} disparado na central!`, 'success');
        } else {
            showToast(`Erro ao disparar pânico: ${res.error || 'Erro desconhecido'}`, 'error');
        }
    } catch (err) {
        console.error(err);
        showToast('Falha ao comunicar disparo.', 'error');
    } finally {
        state.actionPending = false;
        await pollStatus(false);
        startPolling();
    }
}

// ============================================================================
// Modal and Overlay Windows
// ============================================================================

function confirmGlobalAction(action) {
    const isArm = action === 'arm_all';
    
    elements.modalTitle.textContent = isArm ? 'Armar Todas Partições?' : 'Desarmar Todo o Sistema?';
    elements.modalMessage.textContent = isArm 
        ? 'Isso enviará um comando para armar todas as partições ativas de forma simultânea. Confirma?'
        : 'Isso enviará um comando para desarmar imediatamente todo o alarme AMT-8000. Confirma?';
        
    elements.modalConfirmBtn.className = isArm ? 'btn btn-arm btn-sm' : 'btn btn-disarm btn-sm';
    elements.modalConfirmBtn.onclick = () => executeGlobalAction(action);
    
    elements.modalOverlay.classList.remove('hidden');
}

function triggerPanicPrompt() {
    elements.modalTitle.textContent = 'Disparar Alerta de Pânico?';
    elements.modalMessage.textContent = 'Escolha o tipo de disparo de pânico a ser enviado para a central AMT-8000:';
    
    // Customize actions to display panic modes
    const footer = elements.modalOverlay.querySelector('.modal-actions');
    footer.innerHTML = `
        <button class="btn btn-ghost btn-sm" onclick="closeModal()">Cancelar</button>
        <button class="btn btn-disarm btn-sm" onclick="executePanic(2)">Pânico Silencioso</button>
        <button class="btn btn-danger btn-sm" onclick="executePanic(1)"><i class="fa-solid fa-bell"></i> Pânico Sonoro</button>
    `;
    
    elements.modalOverlay.classList.remove('hidden');
}

function closeModal() {
    elements.modalOverlay.classList.add('hidden');
    
    // Restore default cancel/confirm button elements in footer
    const footer = elements.modalOverlay.querySelector('.modal-actions');
    footer.innerHTML = `
        <button id="modal-cancel-btn" class="btn btn-ghost btn-sm" onclick="closeModal()">Cancelar</button>
        <button id="modal-confirm-btn" class="btn btn-arm btn-sm">Confirmar</button>
    `;
    
    // Bind selectors back
    elements.modalConfirmBtn = document.getElementById('modal-confirm-btn');
}

// ============================================================================
// Filtering and Search handlers
// ============================================================================

window.filterZones = function() {
    state.searchQuery = elements.zoneSearch.value;
    if (state.data) {
        const enabledZones = Object.values(state.data.zones || {}).filter(z => z.enabled);
        renderZones(enabledZones);
    }
};

window.setZoneFilter = function(filterType) {
    state.activeFilter = filterType;
    
    // Update toolbar button visual state
    document.querySelectorAll('.filter-btn').forEach(btn => {
        if (btn.getAttribute('data-filter') === filterType) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    if (state.data) {
        const enabledZones = Object.values(state.data.zones || {}).filter(z => z.enabled);
        renderZones(enabledZones);
    }
};

// ============================================================================
// Toast Notification Engine
// ============================================================================

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = 'fa-circle-info';
    if (type === 'success') icon = 'fa-circle-check';
    else if (type === 'error') icon = 'fa-triangle-exclamation';
    else if (type === 'warning') icon = 'fa-bell';

    toast.innerHTML = `
        <span class="toast-icon"><i class="fa-solid ${icon}"></i></span>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    // Auto-remove after 4.5 seconds
    setTimeout(() => {
        toast.classList.add('removing');
        toast.addEventListener('animationend', () => toast.remove());
    }, 4500);
}

// ============================================================================
// Bootstrapping
// ============================================================================

async function init() {
    // 1. Hook retry button click
    elements.btnRetry.addEventListener('click', async () => {
        elements.errorContainer.style.display = 'none';
        elements.loadingOverlay.style.display = 'flex';
        await pollStatus(true);
    });

    // 2. Load configurations
    await fetchConfig();
    
    // 3. Perform initial load and start background updates
    await pollStatus(true);
    startPolling();
}

// Start application
window.addEventListener('DOMContentLoaded', init);
