export const PUBLIC_URL = process.env.PUBLIC_URL || "";
export const API_BASE_URL = process.env.NODE_ENV === "production" ? `${PUBLIC_URL}/api` : "http://127.0.0.1:8000";

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
