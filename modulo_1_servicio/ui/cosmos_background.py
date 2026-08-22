from __future__ import annotations

"""Fondo animado de "cosmos" para NovaSearch.

COSMOS_HEAD es un string de HTML que se inyecta en el <head> de la pagina
(Gradio 6 lo recibe via launch(head=...) / mount_gradio_app(head=...)).
Crea un <canvas> fijo a pantalla completa por detras de la UI con:

  - un starfield parpadeante (240 estrellas),
  - una nebulosa procedural azul/morada como fondo base,
  - una "gema" (diamante) brillante que pulsa y rota,
  - una "estrella heroe" luminosa con rayos y estela que deambula
    (buscando) y orbita la gema cuando se le acerca.

Intenta enriquecer el fondo con puter.js (txt2img) y, si lo logra, dibuja esa
imagen semi-transparente en lugar de la nebulosa procedural. CUALQUIER fallo
de puter (offline, sin auth, etc.) se ignora y la animacion procedural sigue
corriendo. No hay audio.
"""

COSMOS_HEAD: str = """
<script src="https://js.puter.com/v2/puter.js"></script>
<script>
(function () {
  function init() {
    if (document.getElementById('cosmos-canvas')) return;
    var canvas = document.createElement('canvas');
    canvas.id = 'cosmos-canvas';
    canvas.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:-2;pointer-events:none;display:block;';
    document.body.appendChild(canvas);
    var ctx = canvas.getContext('2d');
    var W = 0, H = 0;
    function resize() {
      var dpr = window.devicePixelRatio || 1;
      W = canvas.width = Math.floor(window.innerWidth * dpr);
      H = canvas.height = Math.floor(window.innerHeight * dpr);
    }
    resize();
    window.addEventListener('resize', resize);

    var dpr = window.devicePixelRatio || 1;

    // --- Starfield ---
    var stars = [];
    for (var i = 0; i < 240; i++) {
      stars.push({
        x: Math.random(), y: Math.random(),
        r: Math.random() * 1.4 + 0.3,
        base: Math.random() * 0.5 + 0.3,
        sp: Math.random() * 0.02 + 0.005,
        ph: Math.random() * Math.PI * 2
      });
    }

    // --- Precious object (gem / diamond) ---
    var gem = { x: 0.5, y: 0.55, glow: 0, glowSp: 0.02, rot: 0, rotSp: 0.004 };

    // --- Hero star (searcher) ---
    var hero = { x: 0.2, y: 0.3, tx: 0.7, ty: 0.6, trail: [], orbitAngle: 0, orbiting: false };

    var bgImage = null;

    function pickWaypoint() {
      hero.tx = Math.random() * 0.8 + 0.1;
      hero.ty = Math.random() * 0.8 + 0.1;
    }

    function drawNebula() {
      var g = ctx.createRadialGradient(W * 0.5, H * 0.5, 0, W * 0.5, H * 0.5, Math.max(W, H) * 0.75);
      g.addColorStop(0, '#13183a');
      g.addColorStop(0.45, '#0c1030');
      g.addColorStop(1, '#05060f');
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, H);
      var blobs = [
        [0.3, 0.4, 'rgba(80,60,180,0.20)'],
        [0.7, 0.6, 'rgba(40,90,200,0.18)'],
        [0.5, 0.3, 'rgba(120,50,160,0.14)']
      ];
      for (var i = 0; i < blobs.length; i++) {
        var b = blobs[i];
        var rg = ctx.createRadialGradient(W * b[0], H * b[1], 0, W * b[0], H * b[1], Math.max(W, H) * 0.35);
        rg.addColorStop(0, b[2]);
        rg.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = rg;
        ctx.fillRect(0, 0, W, H);
      }
    }

    function drawDiamond(ctx, x, y, size, rot, pulse) {
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(rot);
      var g = ctx.createLinearGradient(0, -size, 0, size);
      g.addColorStop(0, 'rgba(255,255,255,0.95)');
      g.addColorStop(0.5, 'rgba(150,220,255,0.85)');
      g.addColorStop(1, 'rgba(90,160,255,0.70)');
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.moveTo(0, -size);
      ctx.lineTo(size * 0.65, -size * 0.15);
      ctx.lineTo(0, size);
      ctx.lineTo(-size * 0.65, -size * 0.15);
      ctx.closePath();
      ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,' + (0.85 * pulse).toFixed(3) + ')';
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(-size * 1.2, 0); ctx.lineTo(size * 1.2, 0);
      ctx.moveTo(0, -size * 1.2); ctx.lineTo(0, size * 1.2);
      ctx.stroke();
      ctx.restore();
    }

    function drawHero(ctx, x, y, dpr) {
      var r = 14 * dpr;
      var rg = ctx.createRadialGradient(x, y, 0, x, y, r);
      rg.addColorStop(0, 'rgba(255,255,255,0.95)');
      rg.addColorStop(0.3, 'rgba(150,220,255,0.70)');
      rg.addColorStop(1, 'rgba(120,200,255,0)');
      ctx.fillStyle = rg;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
      ctx.save();
      ctx.translate(x, y);
      ctx.strokeStyle = 'rgba(200,235,255,0.5)';
      ctx.lineWidth = 1;
      for (var k = 0; k < 8; k++) {
        var ang = k * Math.PI / 4;
        ctx.beginPath();
        ctx.moveTo(Math.cos(ang) * r * 0.5, Math.sin(ang) * r * 0.5);
        ctx.lineTo(Math.cos(ang) * r * 1.8, Math.sin(ang) * r * 1.8);
        ctx.stroke();
      }
      ctx.restore();
      ctx.fillStyle = 'rgba(255,255,255,1)';
      ctx.beginPath();
      ctx.arc(x, y, 2.5 * dpr, 0, Math.PI * 2);
      ctx.fill();
    }

    function frame() {
      ctx.clearRect(0, 0, W, H);
      if (bgImage) {
        var ir = bgImage.width / bgImage.height;
        var cr = W / H;
        var dw, dh, dx, dy;
        if (ir > cr) { dh = H; dw = H * ir; dx = (W - dw) / 2; dy = 0; }
        else { dw = W; dh = W / ir; dx = 0; dy = (H - dh) / 2; }
        ctx.globalAlpha = 0.85;
        ctx.drawImage(bgImage, dx, dy, dw, dh);
        ctx.globalAlpha = 1;
      } else {
        drawNebula();
      }

      // Stars
      for (var i = 0; i < stars.length; i++) {
        var s = stars[i];
        s.ph += s.sp;
        var a = s.base + Math.sin(s.ph) * 0.4;
        if (a < 0) a = 0; if (a > 1) a = 1;
        ctx.beginPath();
        ctx.arc(s.x * W, s.y * H, s.r, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255,255,255,' + a.toFixed(3) + ')';
        ctx.fill();
      }

      // Gem glow + diamond
      gem.glow += gem.glowSp;
      var pulse = 0.6 + Math.sin(gem.glow) * 0.4;
      var gx = gem.x * W, gy = gem.y * H;
      var rg2 = ctx.createRadialGradient(gx, gy, 0, gx, gy, 70 * dpr);
      rg2.addColorStop(0, 'rgba(140,220,255,' + (0.55 * pulse).toFixed(3) + ')');
      rg2.addColorStop(0.4, 'rgba(120,170,255,' + (0.22 * pulse).toFixed(3) + ')');
      rg2.addColorStop(1, 'rgba(120,170,255,0)');
      ctx.fillStyle = rg2;
      ctx.beginPath();
      ctx.arc(gx, gy, 70 * dpr, 0, Math.PI * 2);
      ctx.fill();
      gem.rot += gem.rotSp;
      drawDiamond(ctx, gx, gy, 16 * dpr, gem.rot, pulse);

      // Hero movement
      var hx = hero.x * W, hy = hero.y * H;
      var tx = hero.tx * W, ty = hero.ty * H;
      var dx = tx - hx, dy = ty - hy, dist = Math.sqrt(dx * dx + dy * dy);
      var dgx = gx - hx, dgy = gy - hy, dgem = Math.sqrt(dgx * dgx + dgy * dgy);
      if (dgem < 160 * dpr) hero.orbiting = true;

      if (hero.orbiting) {
        hero.orbitAngle += 0.02;
        var orbitR = 90 * dpr;
        var nx = gx + Math.cos(hero.orbitAngle) * orbitR;
        var ny = gy + Math.sin(hero.orbitAngle) * orbitR;
        hero.x = nx / W; hero.y = ny / H;
        if (dgem > 320 * dpr) { hero.orbiting = false; pickWaypoint(); }
      } else {
        hero.x += (hero.tx - hero.x) * 0.012;
        hero.y += (hero.ty - hero.y) * 0.012;
        if (dist < 12 * dpr) pickWaypoint();
      }

      var hx2 = hero.x * W, hy2 = hero.y * H;
      hero.trail.push({ x: hx2, y: hy2 });
      if (hero.trail.length > 18) hero.trail.shift();
      for (var j = 0; j < hero.trail.length; j++) {
        var p = hero.trail[j];
        var ta = (j / hero.trail.length) * 0.5;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 1.5 + (j / hero.trail.length) * 2.5, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(120,200,255,' + ta.toFixed(3) + ')';
        ctx.fill();
      }
      drawHero(ctx, hx2, hy2, dpr);

      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);

    // --- Enrich background with puter.js txt2img (procedural fallback on any failure) ---
    function loadPuterAndGenerate() {
      function generate() {
        try {
          if (!window.puter || !window.puter.ai || !window.puter.ai.txt2img) return;
          window.puter.ai.txt2img(
            "a vast deep-space cosmos, glowing nebula clouds in blue, purple and gold, scattered stars, dark cinematic, no text, no watermark"
          ).then(function (img) {
            if (!img) return;
            var url = img.url || img.src;
            if (!url) return;
            var image = new Image();
            image.crossOrigin = 'anonymous';
            image.onload = function () { bgImage = image; };
            image.onerror = function () { /* keep procedural */ };
            image.src = url;
          }).catch(function () { /* keep procedural */ });
        } catch (e) { /* never break animation */ }
      }
      try {
        if (window.puter && window.puter.ai) {
          generate();
        } else {
          var s = document.createElement('script');
          s.src = 'https://js.puter.com/v2/puter.js';
          s.onload = function () { generate(); };
          s.onerror = function () { /* keep procedural */ };
          document.head.appendChild(s);
        }
      } catch (e) { /* never break animation */ }
    }
    try { loadPuterAndGenerate(); } catch (e) { /* never break animation */ }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
</script>
"""

import re as _re

# Gradio 6.20 ignora el parámetro `head` del constructor de Blocks, pero
# permite registrar JS en el evento `load` del cliente (demo.load(js=...)),
# que funciona tanto en demo.launch() (app.py / HF Spaces) como en
# mount_gradio_app (main.py). Extraemos el cuerpo del IIFE de COSMOS_HEAD y
# lo envolvemos en una arrow function válida para que Gradio lo ejecute.
_COSMOS_MATCH = _re.search(r"\(function \(\) \{(.*)\}\)\(\);", COSMOS_HEAD, _re.DOTALL)
_COSMOS_BODY = _COSMOS_MATCH.group(1).strip() if _COSMOS_MATCH else ""
COSMOS_JS = "() => {\n" + _COSMOS_BODY + "\n}"
