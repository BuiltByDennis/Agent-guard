import { PHASE_PRODUCTION_BUILD } from "next/constants.js";

/** @type {(phase: string) => import('next').NextConfig} */
export default (phase) => {
    // Only a production *build* must fail when the API URL is missing.
    // Throwing at config-load time unconditionally also breaks Jest and
    // `next dev` — and `next lint` loads this file with the production
    // build phase too, so lint is excluded explicitly via argv.
    const isLint = process.argv.includes("lint");
    if (phase === PHASE_PRODUCTION_BUILD && !isLint && !process.env.NEXT_PUBLIC_API_URL) {
        throw new Error("❌ NEXT_PUBLIC_API_URL environment variable is required for production builds. Please set it in your deployment environment.");
    }

    return {
        output: "standalone",
        optimizeFonts: false,
    };
};
