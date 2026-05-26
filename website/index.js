'use strict';
import { API } from './api.js';


let spinningAnimationID = null;

const STATE = {
    RX: 280,
    RY: 170,
    SPEED: 0.05,

    _timers: {},

    tweenValue(key, target, durationMs, ease = true) {
        const start = this[key];
        const delta = target - start;
        const startTime = performance.now();
        cancelAnimationFrame(this._timers[key]);

        const easing = ease ? (t => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t) : (t => t);

        const tick = (ts) => {
            const t = Math.min((ts - startTime) / durationMs, 1);
            this[key] = start + delta * easing(t);
            if (t < 1) {
                this._timers[key] = requestAnimationFrame(tick);
            } else {
                this[key] = target;
                delete this._timers[key];
            }
        };

        this._timers[key] = requestAnimationFrame(tick);
    }
};

function startSpinningAnimation() {
    stopSpinningAnimation();

    const photos = document.querySelectorAll('.photo');
    if (photos.length === 0) return;

    const offsets = Array.from({ length: photos.length }, (_, i) => (360 / photos.length) * i);

    let last = null;
    function animate(ts) {
        if (last === null) last = ts;
        const elapsed = (ts - last) / 1000;
        last = ts;

        offsets.forEach((angle, i) => {
            offsets[i] = (angle + STATE.SPEED * elapsed * 60) % 360;
            const rad = (offsets[i] * Math.PI) / 180;

            const x = Math.cos(rad) * STATE.RX;
            const y = Math.sin(rad) * STATE.RY;

            const photo = photos[i];
            const hw = photo.offsetWidth / 2;
            const hh = photo.offsetHeight / 2;

            const depth = Math.sin(rad);
            const scale = 0.95 + 0.45 * ((depth + 1) / 2);
            photo.style.opacity = 0.7 + 0.5 * ((depth + 1) / 2);
            photo.style.transform = `translate(${x - hw}px, ${y - hh}px) scale(${scale})`;
        });
        spinningAnimationID = requestAnimationFrame(animate);
    }
    spinningAnimationID = requestAnimationFrame(animate);
}

function stopSpinningAnimation() {
    cancelAnimationFrame(spinningAnimationID);
    spinningAnimationID = null;
}

// function playTextEffect(timeMs = 1000, text = '') {
//     const el = document.querySelector('#title');
//     if (text === '') {
//         if (el.innerText.length > 0) {
//             const dur = timeMs / el.innerText.length;
//             function rmChar() {
//                 el.innerText = el.innerText.slice(0, el.innerText.length - 1);
//                 if (el.innerText.length !== 0) setTimeout(rmChar, dur);
//             }
//             rmChar();
//         }
//     } else {
//         el.innerText = '';
//         const dur = timeMs / text.length;
//         function addChar(i) {
//             el.innerText = text.slice(0, i);
//             if (el.innerText.length < text.length) setTimeout(() => addChar(i + 1), dur);
//         }
//         addChar(1);
//     }
// }

// function startCountdown() {
//     const targetDate = new Date('2026-05-29T19:00:00');
//     const el = document.querySelector('#title');

//     function update() {
//         const now = new Date();
//         let diff = Math.max(targetDate - now, 0);

//         const totalSeconds = Math.floor(diff / 1000);
//         const days = Math.floor(totalSeconds / 86400);
//         const hours = Math.floor((totalSeconds % 86400) / 3600);
//         const minutes = Math.floor((totalSeconds % 3600) / 60);
//         const seconds = totalSeconds % 60;

//         const formattedTime =
//             `${String(days).padStart(2, '0')}:` +
//             `${String(hours).padStart(2, '0')}:` +
//             `${String(minutes).padStart(2, '0')}:` +
//             `${String(seconds).padStart(2, '0')}`;

//         el.innerHTML = `ДО ГАЛА-КОНЦЕРТА<br/>${formattedTime}`;
//     }

//     const interval = setInterval(update, 1000);

//     return () => clearInterval(interval);
// }


// Map<id, { url: string, priority: number }>
const imageCache = new Map();

async function refreshConfig() {
    let config;
    try {
        config = await API.getConfig();
    } catch (e) {
        console.error('Failed to load config:', e);
        return;
    }

    const activeIds = new Set(config.map(p => p.id));

    // Remove images no longer in config
    for (const [id, entry] of imageCache) {
        if (!activeIds.has(id)) {
            URL.revokeObjectURL(entry.url);
            imageCache.delete(id);
        }
    }

    // Fetch and cache new images in parallel
    await Promise.all(
        config
            .filter(p => !imageCache.has(p.id))
            .map(async p => {
                try {
                    const url = await API.getImageBlob(p.id);
                    imageCache.set(p.id, { url, priority: 999_999 });
                } catch (e) {
                    console.error(`Failed to load image ${p.id}:`, e);
                }
            })
    );
}

function selectNewImages() {
    if (imageCache.size === 0) return;

    const sorted = [...imageCache.entries()]
        .sort((a, b) => b[1].priority - a[1].priority);

    const minPicCount = 5;
    const maxPicCount = 7;
    const count = Math.min(Math.floor(Math.random() * (maxPicCount - minPicCount + 1)) + minPicCount, sorted.length);
    const selected = sorted.slice(0, count);
    const rest = sorted.slice(count);

    for (const [, entry] of selected) entry.priority = 0;
    for (const [, entry] of rest) entry.priority++;

    document.querySelectorAll('.photo').forEach(el => el.remove());

    const scene = document.querySelector('.scene');

    selected.forEach(cachedImage => {
        const div = document.createElement('div');
        div.classList.add('photo');
        div.style.backgroundImage = `url(${cachedImage[1].url})`;
        div.style.backgroundSize = 'cover';
        div.style.backgroundPosition = 'center';
        scene.appendChild(div);
    });

    startSpinningAnimation();
}

async function init() {

    await refreshConfig();
    selectNewImages();
    // startCountdown();

    const sleep = ms => new Promise((resolve) => setTimeout(resolve, ms));

    const commonRX = 300;
    const commonRY = 200;
    const bigRX = 900;
    const bigRY = 600;
    const transitionMs = 2_000;
    const durationMs = 60_000;

    setInterval(refreshConfig, 60_000);
    setInterval(async () => {
        STATE.tweenValue('RX', bigRX, transitionMs, true);
        STATE.tweenValue('RY', bigRY, transitionMs, true);
        await sleep(transitionMs);
        selectNewImages();
        STATE.tweenValue('RX', commonRX, transitionMs, true);
        STATE.tweenValue('RY', commonRY, transitionMs, true);
    }, durationMs);
}

init();
