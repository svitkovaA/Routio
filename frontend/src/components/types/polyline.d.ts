/**
 * @file polyline.d.ts
 * @brief Type declaration for the polyline decode function
 * @author Andrea Svitkova (xsvitka00)
 */

declare module '@mapbox/polyline' {
  export function decode(str: string): [number, number][];
}

/** End of file polyline.d.ts */
