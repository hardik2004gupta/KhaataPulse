/** @type {import('next').NextConfig} */

const API_URL = (process.env.BACKEND_URL ?? "http://localhost:8000").replace(/\/$/, "");

// standalone output is required for Docker/Render self-hosting.
// On Vercel, VERCEL=1 is set automatically — use Vercel's native build instead.
const isVercel = process.env.VERCEL === "1";

const nextConfig = {
  ...(!isVercel && { output: "standalone" }),

  async rewrites() {
    return [
      // FastAPI serves collection routes only at a trailing slash (`/cases/`),
      // but Next's `:path*` capture drops it. Without this explicit rule the
      // backend answers 307 with an absolute `${BACKEND_URL}/cases/`, which
      // fails in the browser and leaks the internal origin that must stay
      // server-side (CLAUDE.md §20/§21).
      {
        source: "/api/cases",
        destination: `${API_URL}/cases/`,
      },
      {
        source: "/api/:path*",
        destination: `${API_URL}/:path*`,
      },
    ];
  },

  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-Content-Type-Options", value: "nosniff" },
        ],
      },
    ];
  },
};

export default nextConfig;
