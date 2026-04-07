/**
 * @file ElevationUtils.tsx
 * @brief Utility functions for computing elevation profiles
 * @author Andrea Svitkova (xsvitka00)
 */

import type { ElevationPoint } from "../../../../types/types"

// Loaded DEM representation
type TileData = {
    data: Uint8ClampedArray
    width: number
}

const tileCache = new Map<string, TileData>();

/**
 * Resamples a polyline so that points are approximately evenly spaced
 * 
 * @param coordinates Array of geographic coordinates
 * @param stepMeters Desired spacing between resampled points
 * @returns A new array with resampled polyline
 */
export function resamplePolyline(
    coordinates: [number, number][],
    stepMeters: number = 25
): [number, number][] {
    // Resampled coordinates
    const resampled_coords: [number, number][] = [];

    // Iterate through all segments of the polyline
    for (let i = 0; i < coordinates.length - 1; i++) {

        const a = coordinates[i];
        const b = coordinates[i + 1];

        // Compute distance between points in meters
        const distance = haversine_m(a[0], a[1], b[0], b[1]);

        // Determine number of interpolation steps based on desired spacing
        const steps = Math.max(1, Math.floor(distance / stepMeters));

        // Interpolate intermediate points along the segment
        for (let j = 0; j < steps; j++) {

            // Relative position between points
            const t = j / steps;

            // Linear interpolation between points
            resampled_coords.push([
                a[0] + (b[0] - a[0]) * t,
                a[1] + (b[1] - a[1]) * t
            ]);
        }
    }

    // Add final coordinate
    resampled_coords.push(coordinates[coordinates.length - 1]);

    return resampled_coords;
}

/**
 * Computes the great-circle distance between two geographic coordinates using the Haversine formula
 * 
 * @param lat1 Latitude of the first point in degrees
 * @param lon1 Longitude of the first point in degrees
 * @param lat2 Latitude of the second point in degrees
 * @param lon2 Longitude of the second point in degrees
 * @returns Distance between the two points in meters
 */
function haversine_m(
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
): number {
    // Earth radius in meters
    const R = 6371000;

    // Converts coordinates difference to radians
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;

    // Convert original latitudes to radians
    const lat1Rad = lat1 * Math.PI / 180;
    const lat2Rad = lat2 * Math.PI / 180;

    // Haversine formula
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) + Math.cos(lat1Rad) * Math.cos(lat2Rad) * Math.sin(dLon/2) * Math.sin(dLon/2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

    return R * c;
}
/**
 * Computes elevation profile for a sequence of geographic points
 * 
 * @param points Array of geographic coordinates
 * @returns Array of elevation profile points
 */
export async function computeElevation(
    points: [number, number][]
): Promise<ElevationPoint[]> {
    // DEM tile zoom level
    const zoom = 12;

    // Output elevation profile
    const profile: ElevationPoint[] = [];

    // Accumulated distance along the route
    let distance = 0;

    // Process each point of the route
    for (let i = 0; i < points.length; i++) {

        const [lat, lon] = points[i];

        // Convert geographic coordinates to tile coordinates and pixel position within the tile
        const { tileX, tileY, pixelX, pixelY } = latLonToTile(lat, lon, zoom);

        // Load DEM tile
        const tile = tileCache.get(`${zoom}/${tileX}/${tileY}`) ?? await loadTile(zoom, tileX, tileY);

        // Sample terrain elevation from the tile
        const elevation = sampleElevationBilinear(tile, pixelX, pixelY);

        // Compute cumulative route distance
        if (i > 0) {
            const prev = points[i - 1];
            distance += haversine_m(prev[0], prev[1], lat, lon);
        }

        // Add elevation point to the output profile
        profile.push({lat, lon, elevation, distance});
    }

    return profile;
}

/**
 * Converts geographic coordinates to tile coordinates and pixel position within the tile
 * 
 * @param lat Latitude in degrees
 * @param lon Longitude in degrees
 * @param zoom Zoom level of the map
 * @returns Object containing tile indexes with pixel coordinates within the tile
 */
function latLonToTile(
    lat: number,
    lon: number,
    zoom: number
): { tileX: number; tileY: number; pixelX: number; pixelY: number } {

    // Number of tiles per axis at a given zoom level
    const num_of_tiles = 2 ** zoom;

    // Converts longitude into tile coordinates
    const xTile = num_of_tiles * ((lon + 180) / 360);

    // Convert latitude to radians
    const latRad = lat * Math.PI / 180;

    // Convert latitude into tile coordinate using Web Mercator projection ln(tan(lat) + sec(lat))
    const mercatorProjection = Math.log(Math.tan(latRad) + 1 / Math.cos(latRad));
    
    // Normalize to (-1,1)
    const normalizedMercatorProjection = mercatorProjection / Math.PI;

    // Flip axis (north at top, south at bottom)
    const swappedAxes = 1 - normalizedMercatorProjection;

    // Normalize to (0,1)
    const normalizedY = swappedAxes / 2;

    // Convert to tile coordinates
    const yTile = num_of_tiles * normalizedY;

    // Integer tile indices
    const tileX = Math.floor(xTile);
    const tileY = Math.floor(yTile);

    // Pixel position inside the tile
    const pixelX = (xTile - tileX) * 256;
    const pixelY = (yTile - tileY) * 256;

    return { tileX, tileY, pixelX, pixelY };
}

/**
 * Loads a DEM tile from Terrarium dataset
 * 
 * @param z Zoom level of the tile
 * @param x Horizontal tile index
 * @param y Vertical tile index
 * @returns TileData containing raw RGBA pixel data and tile width
 */
async function loadTile(
    z: number,
    x: number,
    y: number
): Promise<TileData> {
    // Unique cache key for the tile
    const key = `${z}/${x}/${y}`;

    // If the tile is already cached, return it
    if (tileCache.has(key)) {
        return tileCache.get(key)!;
    }

    // URL of the Terrarium elevation tile
    const url = `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/${z}/${x}/${y}.png`;

    // Load the tile
    const img = new Image();

    // Allow reading pixel data from the image
    img.crossOrigin = "anonymous";

    // Load and decode image
    img.src = url;
    await img.decode();

    // Create temporary canvas to extract pixel data
    const canvas = document.createElement("canvas");
    canvas.width = 256;
    canvas.height = 256;

    // Get drawing context
    const ctx = canvas.getContext("2d", { willReadFrequently: true })!;

    // Draw the loaded image onto the canvas
    ctx.drawImage(img,0,0);

    // Read raw pixel data inRGBA format
    const image = ctx.getImageData(0, 0, 256, 256);

    // Store tile data
    const tile: TileData = {
        data: image.data,
        width: 256
    };

    // Save tile to cache
    tileCache.set(key, tile);

    return tile;
}

/**
 * Samples terrain elevation from a DEM tile using bilinear interpolation
 * 
 * @param tile DEM tile containing raw RGBA pixel data
 * @param x Horizontal pixel coordinate
 * @param y Vertical pixel coordinate
 * @returns Interpolated elevation value in meters
 */
function sampleElevationBilinear(
    tile: TileData,
    x: number,
    y: number
): number {
    // Coordinates of the top left pixel
    const x0 = Math.floor(x);
    const y0 = Math.floor(y);

    // Coordinates of the bottom right neighbor pixel
    const x1 = Math.min(x0 + 1, 255);
    const y1 = Math.min(y0 + 1, 255);

    // Offsets inside the pixel square
    const dx = x - x0;
    const dy = y - y0;

    // Read RGBA values of the four surrounding pixels
    const p00 = getPixel(tile, x0, y0);
    const p10 = getPixel(tile, x1, y0);
    const p01 = getPixel(tile, x0, y1);
    const p11 = getPixel(tile, x1, y1);

    // Decode elevation from Terrarium RGB encoding
    const e00 = decodeElevation(p00[0], p00[1], p00[2]);
    const e10 = decodeElevation(p10[0], p10[1], p10[2]);
    const e01 = decodeElevation(p01[0], p01[1], p01[2]);
    const e11 = decodeElevation(p11[0], p11[1], p11[2]);

    // Bilinear interpolation between the four elevation values
    return (
        e00 * (1 - dx) * (1 - dy) +
        e10 * dx * (1 - dy) +
        e01 * (1 - dx) * dy +
        e11 * dx * dy
    );
}

/**
 * Reads RGB values of a pixel from a DEM tile
 * 
 * @param tile TileData containing raw RGBA pixel array
 * @param x Horizontal pixel coordinate
 * @param y Vertical pixel coordinate
 * @returns RGB values of the pixel
 */
function getPixel(
    tile: TileData,
    x: number,
    y: number
): [number, number, number] {
    // Compute index of the pixel in the flat RGBA array
    const i = (y * tile.width + x) * 4;

    // Return RGB values
    return [
        tile.data[i],
        tile.data[i + 1],
        tile.data[i + 2]
    ];
}

/**
 * Decodes elevation value from RGB channels of a DEM tile
 * 
 * @param r Red channel value
 * @param g Green channel value
 * @param b Blue channel value
 * @returns Elevation value in meters
 */
function decodeElevation(
    r: number,
    g: number,
    b: number
): number {
    return r * 256 + g + b / 256 - 32768;
}

/**
 * Computes total ascent of a route leg
 * 
 * @param profile Elevation profile containing distance and elevation points
 * @returns Total ascent in meters
 */
export function computeAscent(profile: ElevationPoint[]): number {
    // Smooth elevation values to reduce noise from DEM sampling
    const smoothed = smoothElevationForGain(profile);

    // Total accumulated ascent
    let totalAscent = 0;

    // Accumulated current elevation gain
    let currentGain = 0;

    // Minimum threshold for taking segments gain into account
    const minAscentSegment = 3;

    // Iterates over all points
    for (let i = 1; i < smoothed.length; i++) {
        // Difference between current and previous elevation
        const elevationDifference = smoothed[i].elevation - smoothed[i - 1].elevation;

        // If the route is going uphill
        if (elevationDifference > 0) {
            // Add to the current gain
            currentGain += elevationDifference;
        }
        // End of an uphill segment
        else {
            // Take gain into account if the threshold was reached
            if (currentGain > minAscentSegment) {
                totalAscent += currentGain;
            }
            // Reset current gain
            currentGain = 0;
        }
    }

    // Handle going uphill at the end of the route leg
    if (currentGain > minAscentSegment) {
        totalAscent += currentGain;
    }

    return totalAscent;
}

/**
 * Computes total descent of a route leg
 * 
 * @param profile Elevation profile containing distance and elevation points
 * @returns Total descent in meters
 */
export function computeDescent(profile: ElevationPoint[]): number {
    // Smooth elevation values to reduce noise from DEM sampling
    const smoothed = smoothElevationForGain(profile);

    // Total accumulated descent
    let totalDescent = 0;

    // Accumulated current elevation loss
    let currentLoss = 0;

    // Minimum threshold for taking segments loss into account
    const minDescentSegment = 3;

    // Iterates over all points
    for (let i = 1; i < smoothed.length; i++) {
        // Difference between current and previous elevation
        const elevationDifference = smoothed[i].elevation - smoothed[i - 1].elevation;

        // If the route is going downhill
        if (elevationDifference < 0) {
            // Add to the current loss
            currentLoss += -elevationDifference;
        }
        // End of an downhill segment
        else {
            // Take loss into account if the threshold was reached
            if (currentLoss > minDescentSegment) {
                totalDescent += currentLoss;
            }
            // Reset current loss
            currentLoss = 0;
        }
    }

    // Handle going downhill at the end of the route leg
    if (currentLoss > minDescentSegment) {
        totalDescent += currentLoss;
    }

    return totalDescent;
}

/**
 * Smooth elevation values before computing ascent and descent
 * 
 * @param profile Elevation profile containing distance and elevation points
 * @returns Smoothed elevation profile
 */
function smoothElevationForGain(profile: ElevationPoint[]): ElevationPoint[] {
    // Removes spikes in elevation values
    let smoothed = medianFilter(profile, 3);

    // Smooths elevation curve
    smoothed = gaussianSmooth(smoothed);

    return smoothed;
}

/**
 * Smooth elevation values before visualisation in graph
 * 
 * @param profile Elevation profile containing distance and elevation points
 * @returns Smoothed elevation profile
 */
export function smoothElevationForGraph(profile: ElevationPoint[]): ElevationPoint[] {
    // Removes spikes in elevation values
    let smoothed = medianFilter(profile, 3);

    // Smooths elevation curve
    smoothed = gaussianSmooth(smoothed);
    
    // Smooths elevation curve
    smoothed = gaussianSmooth(smoothed);

    // Smooths elevation profile
    smoothed = distanceSmooth(smoothed);

    return smoothed;
}

/**
 * Applies a median filter to the elevation profile
 * 
 * @param profile Elevation profile containing elevation points
 * @param window Number of neighbors considered on each side
 * @returns Number of neighboring points considered on each side
 */
function medianFilter(profile: ElevationPoint[], window = 5): ElevationPoint[] {
    const filteredProfile = profile.map(p => ({ ...p }));

    // Iterate through all points in the profile
    for (let pointIndex = 0; pointIndex < profile.length; pointIndex++) {

        const neighborElevations: number[] = [];

        // Collect elevation values from the neighborhood window
        for (let offset = -window; offset <= window; offset++) {
            const neighborIndex = pointIndex + offset;

            // Ensure the index stays within profile bounds
            if (neighborIndex >= 0 && neighborIndex < profile.length) {
                neighborElevations.push(profile[neighborIndex].elevation);
            }

        }

        // Sort elevations in ascending order
        neighborElevations.sort((a,b) => a-b);

        // Replace elevation with the median value
        filteredProfile[pointIndex].elevation = neighborElevations[Math.floor(neighborElevations.length/2)];
    }

    return filteredProfile;
}

/**
 * Applies Gaussian smoothing to an elevation profile
 * 
 * @param profile Elevation profile containing elevation points
 * @returns Smoothed elevation profile
 */
function gaussianSmooth(profile: ElevationPoint[]): ElevationPoint[] {
    const smoothedProfile = profile.map(p => ({ ...p }));

    // Discrete Gaussian weights
    const gaussianWeights = [1,4,6,4,1];

    // Sum of discrete Gaussian weights
    const gaussianWeightsSum = 16;

    // Iterates over points
    for (let i = 2; i < profile.length - 2; i++) {
        smoothedProfile[i].elevation = (
            profile[i-2].elevation * gaussianWeights[0] + profile[i-1].elevation * gaussianWeights[1] +
            profile[i].elevation   * gaussianWeights[2] + profile[i+1].elevation * gaussianWeights[3] +
            profile[i+2].elevation * gaussianWeights[4]
        ) / gaussianWeightsSum;
    }

    return smoothedProfile;
}

/**
 * Smooths an elevation profile using distance based weighted averaging
 * 
 * @param profile Elevation profile containing distance and elevation points
 * @param window Maximum distance in meters used for smoothing
 * @returns Smoothed elevation profile
 */
function distanceSmooth(
    profile: ElevationPoint[],
    window = 80
): ElevationPoint[] {
    const smoothedProfile = profile.map(p => ({ ...p }));

    // Iterate over all points
    for (let pointIndex = 0; pointIndex < profile.length; pointIndex++) {
        // Distance of the current point along the route
        const centerDistance = profile[pointIndex].distance;
        
        // Accumulates weighted elevation values
        let weightedElevationSum = 0;

        // Accumulates weights for normalization
        let totalWeight = 0;

        // Compare the current point with all other points
        for (let neighborIndex = 0; neighborIndex < profile.length; neighborIndex++) {
            // Distance between the current point and a neighboring point
            const distanceFromCenter = Math.abs(profile[neighborIndex].distance - centerDistance);

            // Only consider neighbors within the smoothing window
            if (distanceFromCenter <= window) {
                // Linear weight decreasing with distance
                const weight = 1 - distanceFromCenter / window;

                // Add weighted elevation contribution
                weightedElevationSum += profile[neighborIndex].elevation * weight;

                // Accumulate weights
                totalWeight += weight;
            }
        }

        // Compute the weighted average elevation
        smoothedProfile[pointIndex].elevation = weightedElevationSum / totalWeight;
    }

    return smoothedProfile;
}

/** End of file ElevationUtils.tsx */
