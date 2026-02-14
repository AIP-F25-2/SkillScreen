/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
        port: '',
        pathname: '/**',
      },
    ],
  },
  webpack: (config, { isServer }) => {
    // Disable webpack cache to avoid hanging issues
    config.cache = false;
    return config;
  },
  async rewrites() {
    return [
      {
        source: '/api-proxy/:path*',
        destination: 'http://4.206.209.183:80/:path*',
      },
    ]
  },
}

module.exports = nextConfig
