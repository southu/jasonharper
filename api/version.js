module.exports = function handler(req, res) {
  const sha = String(process.env.VERCEL_GIT_COMMIT_SHA || "").trim();
  res.setHeader("Content-Type", "text/plain; charset=utf-8");
  res.setHeader("Cache-Control", "no-store, no-cache, must-revalidate");
  res.setHeader("Pragma", "no-cache");
  res.status(200).send(sha + "\n");
};
