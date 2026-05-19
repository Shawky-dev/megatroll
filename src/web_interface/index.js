// ─────────────────────────────────────────────────────────────────────────────
// ROS2 Differential Drive Joystick Controller
//
// Mixing algorithm (ImpulseAdventure / classic differential steering):
//   raw_left  = Y + X
//   raw_right = Y - X
//   Then normalize: if either exceeds ±1, divide BOTH by the larger magnitude.
//   This preserves the turn ratio at full throttle instead of clipping one side.
//
// The joystick sends left/right motor PWM directly as a custom UART packet
// via the ROS node. angular/linear in TwistStamped carry the motor values.
// ─────────────────────────────────────────────────────────────────────────────

// ─── Config ──────────────────────────────────────────────────────────────────
const ROS_URL = 'ws://zeyadcodepi.local:9090';
const PUBLISH_HZ = 20;      // send rate in Hz
const RECONNECT_MS = 2000;
const STOP_DELAY = 100;     // ms after release before sending stop

// Dead zone: ignore joystick inputs smaller than this (normalized 0-1).
// Prevents motor buzz when the stick rests slightly off-center.
const DEAD_ZONE = 0.05;

// Expo curve exponent. 1.0 = linear, 2.0 = quadratic (recommended).
// Makes low-speed control finer without reducing max speed.
const EXPO = 2.0;

// Pivot-Y limit: when |Y| is below this threshold (0-1) and |X| is non-zero,
// the robot pivots in place (one motor fwd, one rev).
// Above this threshold it arc-turns instead.
// 0.0 = always arc, 1.0 = always pivot. ~0.2 is a good starting point.
const PIVOT_Y_LIMIT = 0.2;

// ─── DOM ─────────────────────────────────────────────────────────────────────
const statusDiv = document.getElementById('statusMsg');
const canvas = document.getElementById('joystickCanvas');
const speedSlider = document.getElementById('speedScale');
const linearOut = document.getElementById('linearVal');
const angularOut = document.getElementById('angularVal');

let speedScale = parseFloat(speedSlider.value);
speedSlider.addEventListener('input', e => { speedScale = parseFloat(e.target.value); });

// ─── ROS2 ────────────────────────────────────────────────────────────────────
const ros = new ROSLIB.Ros({ url: ROS_URL });
let reconnectTimer = null;

function setConnected(ok) {
    canvas.style.opacity = ok ? '1' : '0.45';
    canvas.style.pointerEvents = ok ? 'auto' : 'none';
    if (ok) {
        clearInterval(reconnectTimer); reconnectTimer = null;
        statusDiv.textContent = '✅ Connected'; statusDiv.className = 'connected';
    } else if (!reconnectTimer) {
        reconnectTimer = setInterval(() => ros.connect(ROS_URL), RECONNECT_MS);
    }
}

ros.on('connection', () => setConnected(true));
ros.on('error', err => { statusDiv.textContent = `❌ ${err}`; statusDiv.className = 'error'; setConnected(false); });
ros.on('close', () => { statusDiv.textContent = '⚠️ Reconnecting…'; statusDiv.className = 'disconnected'; setConnected(false); });

const cmdVelTopic = new ROSLIB.Topic({
    ros, name: '/cmd_vel', messageType: 'geometry_msgs/TwistStamped',
});

// Publish left/right motor values (-1…+1) packed into linear.x and angular.z.
// The ROS node on the Pi unpacks these and forwards them as raw PWM over UART.
function publishMotors(left, right) {
    if (!ros.isConnected) return;
    cmdVelTopic.publish(new ROSLIB.Message({
        header: { stamp: { sec: 0, nanosec: 0 }, frame_id: 'base_link' },
        twist: {
            linear: { x: left, y: 0, z: 0 },
            angular: { x: 0, y: 0, z: right },
        },
    }));
    if (linearOut) linearOut.textContent = (left * 100).toFixed(0);
    if (angularOut) angularOut.textContent = (right * 100).toFixed(0);
}

// ─── Mixing ──────────────────────────────────────────────────────────────────
// x: -1 (left) … +1 (right)
// y: -1 (back) … +1 (forward)
// Returns { left, right } each in -1…+1
function mix(x, y) {
    // 1. Dead zone — applied per axis before mixing
    const dx = Math.abs(x) < DEAD_ZONE ? 0 : Math.sign(x) * (Math.abs(x) - DEAD_ZONE) / (1 - DEAD_ZONE);
    const dy = Math.abs(y) < DEAD_ZONE ? 0 : Math.sign(y) * (Math.abs(y) - DEAD_ZONE) / (1 - DEAD_ZONE);

    // 2. Expo curve — finer low-speed control
    const ex = Math.sign(dx) * Math.pow(Math.abs(dx), EXPO);
    const ey = Math.sign(dy) * Math.pow(Math.abs(dy), EXPO);

    // 3. Pivot vs arc mixing
    // When barely moving forward (|ey| < PIVOT_Y_LIMIT) and turning,
    // blend toward a full pivot so the robot can spin in place cleanly.
    let left, right;
    const pivotBlend = Math.max(0, 1 - Math.abs(ey) / PIVOT_Y_LIMIT); // 1 at y=0, 0 at y=PIVOT_Y_LIMIT

    if (Math.abs(ey) < PIVOT_Y_LIMIT && Math.abs(ex) > 0.01) {
        // Pivot in place: left and right spin opposite directions
        const pivot = ex * pivotBlend;
        const arc_l = ey + ex * (1 - pivotBlend);
        const arc_r = ey - ex * (1 - pivotBlend);
        left = pivot + arc_l * (1 - pivotBlend);
        right = -pivot + arc_r * (1 - pivotBlend);
    } else {
        // Standard differential mixing
        left = ey + ex;
        right = ey - ex;
    }

    // 4. Normalize — if either side exceeds ±1, scale BOTH down by the same
    //    factor so the turn ratio is preserved (not clipped).
    const maxVal = Math.max(Math.abs(left), Math.abs(right));
    if (maxVal > 1.0) { left /= maxVal; right /= maxVal; }

    // 5. Apply speed scale
    return { left: left * speedScale, right: right * speedScale };
}

// ─── Joystick canvas ─────────────────────────────────────────────────────────
const SIZE = canvas.width;
const CX = SIZE / 2, CY = SIZE / 2;
const MAX_R = SIZE * 0.32;
const KNOB_R = SIZE * 0.11;
const ctx = canvas.getContext('2d');

let joyX = 0, joyY = 0, isActive = false;

function drawJoystick() {
    ctx.clearRect(0, 0, SIZE, SIZE);

    // Base
    ctx.beginPath(); ctx.arc(CX, CY, MAX_R + 6, 0, Math.PI * 2);
    ctx.fillStyle = '#1a2630'; ctx.fill();
    ctx.beginPath(); ctx.arc(CX, CY, MAX_R, 0, Math.PI * 2);
    ctx.fillStyle = '#2c3e4a'; ctx.fill();
    ctx.strokeStyle = '#4a6070'; ctx.lineWidth = 1.5; ctx.stroke();

    // Crosshairs
    ctx.setLineDash([4, 6]); ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(CX - MAX_R, CY); ctx.lineTo(CX + MAX_R, CY);
    ctx.moveTo(CX, CY - MAX_R); ctx.lineTo(CX, CY + MAX_R);
    ctx.stroke(); ctx.setLineDash([]);

    // Knob — clamped to circle
    let kx = CX + joyX * MAX_R;
    let ky = CY - joyY * MAX_R;
    const d = Math.hypot(kx - CX, ky - CY);
    if (d > MAX_R) { kx = CX + (kx - CX) / d * MAX_R; ky = CY + (ky - CY) / d * MAX_R; }

    if (isActive) { ctx.shadowColor = '#e67e22aa'; ctx.shadowBlur = 18; }
    ctx.beginPath(); ctx.arc(kx, ky, KNOB_R, 0, Math.PI * 2);
    ctx.fillStyle = '#c0622a'; ctx.fill();
    ctx.beginPath(); ctx.arc(kx, ky, KNOB_R * 0.78, 0, Math.PI * 2);
    ctx.fillStyle = '#e67e22'; ctx.fill();
    ctx.shadowBlur = 0;

    // Center dot
    ctx.beginPath(); ctx.arc(CX, CY, 3, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(255,255,255,0.2)'; ctx.fill();
}

function toNorm(clientX, clientY) {
    const r = canvas.getBoundingClientRect();
    let dx = (clientX - r.left) * (SIZE / r.width) - CX;
    let dy = (clientY - r.top) * (SIZE / r.height) - CY;
    const dist = Math.hypot(dx, dy);
    if (dist > MAX_R) { dx = dx / dist * MAX_R; dy = dy / dist * MAX_R; }
    return { x: dx / MAX_R, y: -dy / MAX_R };
}

// ─── Publish loop ────────────────────────────────────────────────────────────
let publishTimer = null, stopTimer = null;

function startPublishing() {
    if (publishTimer) return;
    publishTimer = setInterval(() => {
        if (!isActive) return;
        const { left, right } = mix(joyX, joyY);
        publishMotors(left, right);
    }, 1000 / PUBLISH_HZ);
}

function stopPublishing() {
    if (publishTimer) { clearInterval(publishTimer); publishTimer = null; }
}

// ─── Events ──────────────────────────────────────────────────────────────────
function onStart(e) {
    if (!ros.isConnected) return;
    e.preventDefault();
    clearTimeout(stopTimer); stopTimer = null;
    isActive = true;
    const pt = e.touches ? e.touches[0] : e;
    ({ x: joyX, y: joyY } = toNorm(pt.clientX, pt.clientY));
    drawJoystick(); startPublishing();
}

function onMove(e) {
    if (!isActive) return;
    e.preventDefault();
    const pt = e.touches ? e.touches[0] : e;
    ({ x: joyX, y: joyY } = toNorm(pt.clientX, pt.clientY));
    drawJoystick();
}

function onEnd(e) {
    if (!isActive) return;
    e.preventDefault();
    isActive = false; joyX = 0; joyY = 0;
    drawJoystick(); stopPublishing();
    stopTimer = setTimeout(() => { publishMotors(0, 0); stopTimer = null; }, STOP_DELAY);
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
