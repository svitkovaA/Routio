import { defineConfig, loadEnv } from 'vite';

export default ({ mode } : { mode: string }) => {
    const env = loadEnv(mode, process.cwd());
    return defineConfig({
        base: env.VITE_BASE_URL || "/"
    });
};
