// Reachability search using the game's own player physics.
// Static spikes are lethal; timed / moving hazards are ignored (they are a timing matter).
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 620, height: 1000 } });
  const errs = []; pg.on('pageerror', e => errs.push(e.message));
  await pg.goto('file://' + require('path').resolve(__dirname, '..', 'index.html'));
  await pg.waitForTimeout(800);
  const res = await pg.evaluate(() => {
    muted = true; state = 'play';
    placePlayerAt(START);
    const snap = () => Object.assign({}, player);
    const heap = []; // min-heap on y
    const push = n => { heap.push(n); let i = heap.length - 1; while (i > 0) { const p = (i - 1) >> 1; if (heap[p].y <= heap[i].y) break; [heap[p], heap[i]] = [heap[i], heap[p]]; i = p; } };
    const pop = () => { const top = heap[0], last = heap.pop(); if (heap.length) { heap[0] = last; let i = 0; for (;;) { let l = 2 * i + 1, r = l + 1, m = i; if (l < heap.length && heap[l].y < heap[m].y) m = l; if (r < heap.length && heap[r].y < heap[m].y) m = r; if (m === i) break; [heap[m], heap[i]] = [heap[i], heap[m]]; i = m; } } return top; };
    const key = p => [p.x >> 2, p.y >> 2, Math.round(p.vx / 80), Math.round(p.vy / 120), p.small ? 1 : 0, p.onGround ? 1 : 0, p.lock > 0 ? 1 : 0].join(',');
    const seen = new Set();
    const s0 = snap(); seen.add(key(s0)); push(s0);
    let n = 0, best = s0.y, won = false;
    const marks = checkpoints.map(c => ({ y: c.y, hit: false }));
    while (heap.length && n < 4000000 && !won) {
      const cur = pop(); n++;
      for (let d = -1; d <= 1 && !won; d++) for (let j = 0; j < 2 && !won; j++) for (let sh = 0; sh < 2; sh++) {
        Object.assign(player, cur);
        keys.left = d < 0; keys.right = d > 0; keys.shrink = !!sh;
        if (j) player.jumpBuf = BUFFER;
        let dead = false;
        for (let k = 0; k < 6 && !dead; k++) {
          updatePlayer(1 / 120);
          const hb = hitbox();
          for (const s of spikes) if (overlap(hb, s)) { dead = true; break; }
        }
        particles.length = 0;
        if (dead) continue;
        const hb = hitbox();
        if (overlap(hb, { x: GOAL.x - 14, y: GOAL.y - 34, w: 28, h: 34 })) { won = true; break; }
        const kk = key(player);
        if (seen.has(kk)) continue;
        seen.add(kk);
        if (player.y < best) best = player.y;
        for (const m of marks) if (!m.hit && overlap(hb, { x: checkpoints[marks.indexOf(m)].x - 12, y: m.y - 48, w: 24, h: 48 })) m.hit = true;
        push(snap());
      }
    }
    const bestRowBottomUp = ROWS - 1 - Math.floor(best / T);
    return { won, expansions: n, states: seen.size, bestRowBottomUp, rows: ROWS, checkpointsReached: marks.filter(m => m.hit).length + '/' + marks.length,
             stuckBelow: won ? null : MAP.slice(Math.max(0, Math.floor(best / T) - 6), Math.floor(best / T) + 3) };
  });
  console.log(JSON.stringify(res, null, 1), errs);
  await b.close();
})();
