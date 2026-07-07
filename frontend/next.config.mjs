if (!process.env.NEXT_PUBLIC_API_URL && process.env.NODE_ENV !== 'development') {
    throw new Error("❌ NEXT_PUBLIC_API_URL environment variable is required for production builds. Please set it in your deployment environment.");
}

/** @type {import('next').NextConfig} */
const nextConfig = {
    output: "standalone",
    optimizeFonts: false,
};

export default nextConfig;
