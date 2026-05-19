'use strict'

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

        const easing = ease ? (t => t < 0.5 ? 2*t*t : -1+(4-2*t)*t) : (t => t);

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

            const depth = Math.sin(rad); // -1..1
            // photo.style.zIndex = Math.floor(y);
            const scale = 0.65 + 0.45 * ((depth + 1) / 2);
            photo.style.opacity = 0.5 + 0.5 * ((depth + 1) / 2);

            photo.style.transform =
                `translate(${x - hw}px, ${y - hh}px) scale(${scale})`;
        });
        spinningAnimationID = requestAnimationFrame(animate);
    }
    spinningAnimationID = requestAnimationFrame(animate);
}

function stopSpinningAnimation() {
    cancelAnimationFrame(spinningAnimationID);
    spinningAnimationID = null;
}

function playTextEffect(timeMs = 1000, text = '') {
    const el = document.querySelector('#title');
    if (text === '') {
        if (el.innerText.length > 0) {
            const dur = timeMs / el.innerText.length
            function rmChar() {
                el.innerText = el.innerText.slice(0, el.innerText.length - 1);
                if (el.innerText.length !== 0) {
                    setTimeout(rmChar, dur);
                }
            }
            rmChar();
        }
    } else {
        el.innerText = '';
        const dur = timeMs / text.length;
        function addChar(i) {
            el.innerText = text.slice(0, i);
            if (el.innerText.length < text.length) {
                setTimeout(() => addChar(i + 1), dur);
            }
        }
        addChar(1);
    }
}

