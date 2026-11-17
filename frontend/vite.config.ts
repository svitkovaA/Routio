import { defineConfig, loadEnv } from 'vite';

export default ({ mode } : { mode: string }) => {
    const env = loadEnv(mode, process.cwd());
    return defineConfig({
        // Vite expects a trailing slash; without it `${BASE_URL}img/...` becomes "/routioimg/...".
        base: (env.VITE_BASE_URL || "/").replace(/\/?$/, "/")
    });
};
