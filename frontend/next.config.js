/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  webpack: (config, { isServer }) => {
    // Disable webpack cache to avoid hanging issues
    config.cache = false;
    return config;
  },
}

module.exports = nextConfig
