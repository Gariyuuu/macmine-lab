function parseCookies(header) {
  const out = {};
  (header || "").split(";").forEach((pair) => {
    const idx = pair.indexOf("=");
    if (idx === -1) return;
    const k = pair.slice(0, idx).trim();
    const v = pair.slice(idx + 1).trim();
    out[k] = v;
  });
  return out;
}

const GUIDE_HTML = `
<h2>When can you actually use it?</h2>
<p class="lead">Right now — it's not a future thing. Everything is already installed and working on this Mac from testing.</p>

<h3>Already done (nothing to install)</h3>
<ul>
  <li>XMRig and monerod both installed via Homebrew</li>
  <li>Backend venv and frontend deps ready</li>
  <li>All 180 backend tests pass, both apps build clean</li>
</ul>

<h3>To start it up</h3>
<div class="cli"><span class="c">$</span> cd ~/Projects/macmine-lab<br/><span class="c">$</span> ./dev.sh<span class="c">   # starts backend (127.0.0.1:8834) + dashboard (localhost:3000) together</span></div>
<p>Then open <code>http://localhost:3000</code>.</p>

<h3>What you can do immediately</h3>
<ul>
  <li><code>./macmine benchmark --duration 30</code> — real hashing, no setup needed</li>
  <li>Dashboard, Journal, Analytics pages — already have live data from testing</li>
</ul>

<h3>Before real mining pays out to you</h3>
<p>The wallet and pool currently in the local database are synthetic test values used to verify the flow — not a real address. Go to <code>/setup</code> in the dashboard and:</p>
<ol>
  <li>Enter your real Monero wallet address (official Monero GUI/CLI, Cake Wallet, whatever you use)</li>
  <li>Add a real pool — no preset is shipped on purpose; check the pool's own site for current host/port (e.g. supportxmr.com)</li>
  <li>Remove the old test wallet/pool via the "Remove" buttons</li>
</ol>
<p>Then it's real: click Start Mining, real shares get submitted, real XMR accrues to your address.</p>

<h3>Going fully decentralized</h3>
<p>The <code>/p2pool</code> page is the one place with a real cost gate — a 60GB+ blockchain download — so that's a "when you're ready" thing, not a "right now" thing.</p>

<h3>Everything else is already live</h3>
<p>Safety automation, thermal protection, and First Penny tracking all activate the moment you start mining. No additional build work needed.</p>
`;

module.exports = async (req, res) => {
  const cookies = parseCookies(req.headers.cookie);
  const token = process.env.GUIDE_SESSION_TOKEN || "";

  if (!token || cookies.guide_session !== token) {
    res.status(401).json({ error: "Not authenticated" });
    return;
  }

  res.status(200).json({ html: GUIDE_HTML });
};
