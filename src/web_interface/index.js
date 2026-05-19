// ─────────────────────────────────────────────────────────────────────────────
// ROS2 Joystick Controller
// Publishes geometry_msgs/TwistStamped on /cmd_vel
// PWM range sent: -100 … +100 (mapped from joystick position)
// ─────────────────────────────────────────────────────────────────────────────

// ─── Config ──────────────────────────────────────────────────────────────────
const ROS_URL = 'ws://zeyadcodepi.local:9090';
const PUBLISH_HZ = 20;           // Hz — how often to send commands
const RECONNECT_MS = 2000;         // ms between reconnect attempts
const STOP_DELAY_MS = 100;          // ms after release before sending stop (debounce)

// ─── DOM refs ────────────────────────────────────────────────────────────────
const statusDiv = document.getElementById('statusMsg');
const canvas = document.getElementById('joystickCanvas');
const speedSlider = document.getElementById('speedScale');
const linearOut = document.getElementById('linearVal');
const angularOut = document.getElementById('angularVal');

// ─── ROS2 connection ─────────────────────────────────────────────────────────
const ros = new ROSLIB.Ros({ url: ROS_URL });
let reconnectTimer = null;

function setConnected(connected) {
    if (connected) {
        clearInterval(reconnectTimer);
        reconnectTimer = null;
        statusDiv.textContent = '✅ Connected';
        statusDiv.className = 'connected';
        canvas.style.opacity = '1';
        canvas.style.pointerEvents = 'auto';
    } else {
        canvas.style.opacity = '0.45';
        canvas.style.pointerEvents = 'none';
        if (!reconnectTimer) {
            reconnectTimer = setInterval(() => ros.connect(ROS_URL), RECONNECT_MS);
        }
    }
}

ros.on('connection', () => {
    setConnected(true);
    statusDiv.textContent = '✅ Connected';
});
ros.on('error', (err) => {
    statusDiv.textContent = `❌ Error: ${err}`;
    statusDiv.className = 'error';
    setConnected(false);
});
ros.on('close', () => {
    statusDiv.textContent = '⚠️ Disconnected – reconnecting…';
    statusDiv.className = 'disconnected';
    setConnected(false);
});

// ─── Publisher ───────────────────────────────────────────────────────────────
const cmdVelTopic = new ROSLIB.Topic({
    ros,
    name: '/cmd_vel',
    messageType: 'geometry_msgs/TwistStamped',
});

function publishTwist(linear, angular) {
    if (!ros.isConnected) return;

    // TwistStamped requires a header
    const msg = new ROSLIB.Message({
        header: {
            stamp: { sec: 0, nanosec: 0 },  // rosbridge fills this if left at 0
            frame_id: 'base_link',
        },
        twist: {
            linear: { x: linear, y: 0, z: 0 },
            angular: { x: 0, y: 0, z: angular },
        },
    });

    cmdVelTopic.publish(msg);

    if (linearOut) linearOut.textContent = linear.toFixed(3);
    if (angularOut) angularOut.textContent = angular.toFixed(3);
}

// ─── Joystick geometry ───────────────────────────────────────────────────────
const SIZE = canvas.width;          // assumes square canvas
const CX = SIZE / 2;
const CY = SIZE / 2;
const MAX_R = SIZE * 0.32;           // dead zone begins at pixel 0 from center
const KNOB_R = SIZE * 0.11;
const DEAD_ZONE = 0.04;                  // normalized, ignore tiny inputs

let joyNormX = 0;   // -1 … +1  (right = positive)
let joyNormY = 0;   // -1 … +1  (forward = positive)
let isActive = false;

// ─── Canvas drawing ──────────────────────────────────────────────────────────
const ctx = canvas.getContext('2d');

function drawJoystick() {
    ctx.clearRect(0, 0, SIZE, SIZE);

    // Base ring
    ctx.beginPath();
    ctx.arc(CX, CY, MAX_R + 6, 0, Math.PI * 2);
    ctx.fillStyle = '#1a2630';
    ctx.fill();

    ctx.beginPath();
    ctx.arc(CX, CY, MAX_R, 0, Math.PI * 2);
    ctx.fillStyle = '#2c3e4a';
    ctx.fill();
    ctx.strokeStyle = '#4a6070';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Crosshair
    ctx.setLineDash([4, 6]);
    ctx.strokeStyle = 'rgba(255,255,255,0.15)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(CX - MAX_R, CY); ctx.lineTo(CX + MAX_R, CY);
    ctx.moveTo(CX, CY - MAX_R); ctx.lineTo(CX, CY + MAX_R);
    ctx.stroke();
    ctx.setLineDash([]);

    // Knob — clamped to circle
    let kx = CX + joyNormX * MAX_R;
    let ky = CY - joyNormY * MAX_R;
    const dist = Math.hypot(kx - CX, ky - CY);
    if (dist > MAX_R) {
        kx = CX + ((kx - CX) / dist) * MAX_R;
        ky = CY + ((ky - CY) / dist) * MAX_R;
    }

    // Shadow glow when active
    if (isActive) {
        ctx.shadowColor = '#e67e22aa';
        ctx.shadowBlur = 18;
    }

    ctx.beginPath();
    ctx.arc(kx, ky, KNOB_R, 0, Math.PI * 2);
    ctx.fillStyle = '#c0622a';
    ctx.fill();

    ctx.beginPath();
    ctx.arc(kx, ky, KNOB_R * 0.78, 0, Math.PI * 2);
    ctx.fillStyle = '#e67e22';
    ctx.fill();

    ctx.shadowBlur = 0;

    // Center dot
    ctx.beginPath();
    ctx.arc(CX, CY, 3, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,255,255,0.25)';
    ctx.fill();
}

// ─── Input → normalized coords ───────────────────────────────────────────────
function toNormalized(clientX, clientY) {
    const rect = canvas.getBoundingClientRect();
    const sx = SIZE / rect.width;
    const sy = SIZE / rect.height;
    let dx = (clientX - rect.left) * sx - CX;
    let dy = (clientY - rect.top) * sy - CY;

    // Clamp to circle
    const dist = Math.hypot(dx, dy);
    if (dist > MAX_R) {
        dx = (dx / dist) * MAX_R;
        dy = (dy / dist) * MAX_R;
    }

    return {
        x: dx / MAX_R,          //  right = +1
        y: -dy / MAX_R,          //  up    = +1  (canvas Y is inverted)
    };
}

// ─── Apply dead zone ─────────────────────────────────────────────────────────
function applyDeadZone(v) {
    if (Math.abs(v) < DEAD_ZONE) return 0;
    // Re-scale so output starts from 0 just outside dead zone
    return (v - Math.sign(v) * DEAD_ZONE) / (1 - DEAD_ZONE);
}

// ─── Publish loop (fixed rate) ────────────────────────────────────────────────
let publishTimer = null;
let stopTimer = null;

function startPublishing() {
    if (publishTimer) return;
    publishTimer = setInterval(() => {
        if (!isActive) return;

        const speedScale = parseFloat(speedSlider.value);

        // Apply dead zone, then scale by speed slider
        const vx = applyDeadZone(joyNormX) * speedScale;  // lateral: right = +
        const vy = applyDeadZone(joyNormY) * speedScale;  // longitudinal: fwd = +

        // Differential drive:
        //   linear  = forward component
        //   angular = turning component (left = positive in ROS)
        const linear = vy;
        const angular = -vx;   // joystick right → negative angular (turn right)

        publishTwist(linear, angular);
    }, 1000 / PUBLISH_HZ);
}

function stopPublishing() {
    if (publishTimer) {
        clearInterval(publishTimer);
        publishTimer = null;
    }
}

// ─── Event handlers ───────────────────────────────────────────────────────────
function onStart(e) {
    if (!ros.isConnected) return;
    e.preventDefault();

    clearTimeout(stopTimer);
    stopTimer = null;

    isActive = true;
    const pt = e.touches ? e.touches[0] : e;
    ({ x: joyNormX, y: joyNormY } = toNormalized(pt.clientX, pt.clientY));
    drawJoystick();
    startPublishing();
}

function onMove(e) {
    if (!isActive) return;
    e.preventDefault();
    const pt = e.touches ? e.touches[0] : e;
    ({ x: joyNormX, y: joyNormY } = toNormalized(pt.clientX, pt.clientY));
    drawJoystick();
}

function onEnd(e) {
    if (!isActive) return;
    e.preventDefault();
    isActive = false;
    joyNormX = 0;
    joyNormY = 0;
    drawJoystick();
    stopPublishing();

    // Send a final stop command after a short debounce
    stopTimer = setTimeout(() => {
        publishTwist(0, 0);
        stopTimer = null;
    }, STOP_DELAY_MS);
}

canvas.addEventListener('mousedown', onStart);
window.addEventListener('mousemove', onMove);
window.addEventListener('mouseup', onEnd);

canvas.addEventListener('touchstart', onStart, { passive: false });
window.addEventListener('touchmove', onMove, { passive: false });
window.addEventListener('touchend', onEnd, { passive: false });

// ─── Init ─────────────────────────────────────────────────────────────────────
setConnected(false);
drawJoystick();
