module.exports = function handler(req, res) {
  const sha = process.env.VERCEL_GIT_COMMIT_SHA || "";
  res.setHeader("Content-Type", "text/plain; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  res.status(200).send(String(sha) + "\n");
};
