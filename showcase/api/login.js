const crypto = require("crypto");

function timingSafeEqual(a, b) {
  const bufA = Buffer.from(a);
  const bufB = Buffer.from(b);
  if (bufA.length !== bufB.length) return false;
  return crypto.timingSafeEqual(bufA, bufB);
}

module.exports = async (req, res) => {
  if (req.method !== "POST") {
    res.status(405).json({ error: "Method not allowed" });
    return;
  }

  let body = req.body;
  if (!body || typeof body === "string") {
    try {
      body = JSON.parse(body || "{}");
    } catch {
      body = {};
    }
  }

  const password = String(body.password || "");
  const expected = process.env.GUIDE_PASSWORD || "";
  const token = process.env.GUIDE_SESSION_TOKEN || "";

  if (!expected || !token) {
    res.status(500).json({ error: "Server not configured" });
    return;
  }

  if (!password || !timingSafeEqual(password, expected)) {
    res.status(401).json({ error: "Incorrect password" });
    return;
  }

  res.setHeader(
    "Set-Cookie",
    `guide_session=${token}; HttpOnly; Secure; SameSite=Strict; Max-Age=2592000; Path=/`
  );
  res.status(200).json({ ok: true });
};
