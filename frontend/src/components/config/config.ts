export const PUBLIC_URL = import.meta.env.BASE_URL;
export const API_BASE_URL = import.meta.env.VITE_API_URL || `${import.meta.env.BASE_URL.replace(/\/$/, '')}/api`;

// Praha + JMK + Olomouc
// export const NW_LAT = 50.6;
// export const NW_LON = 13.3;
// export const SE_LAT = 48.6;
// export const SE_LON = 17.9;

// JMK
export const NW_LAT = 49.6332550;
export const NW_LON = 15.5424248;
export const SE_LAT = 48.6165408;
export const SE_LON = 17.6469364;
