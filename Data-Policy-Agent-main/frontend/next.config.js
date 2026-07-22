/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "https://data-policy-agent.onrender.com/api/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
