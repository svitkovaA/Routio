/**
 * @file ElevationProfile.tsx
 * @brief Displays an elevation profile chart
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from "react";
import ReactApexChart from "react-apexcharts";
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import LandscapeIcon from '@mui/icons-material/Landscape';
import { PolyInfo } from "../../../../types/types";
import { useResult } from "../../../../Contexts/ResultContext";
import NorthEastIcon from '@mui/icons-material/NorthEast';
import SouthEastIcon from '@mui/icons-material/SouthEast';
import CustomTooltip from "../../../../CustomTooltip/CustomTooltip";
import { useTranslation } from "react-i18next";
import "./ElevationProfile.css"

type ElevationProfileProps = {
    polyInfo?: PolyInfo;                        // Elevation and polyline data for the current leg
    legIndex: number;                           // Index of the leg whose elevation profile is displayed
    openElevation: (value: boolean) => void;    // Callback used to toggle visibility of the elevation profile
};

export default function ElevationProfile({
    polyInfo,
    legIndex,
    openElevation
}: ElevationProfileProps) {
    // Translation function
    const { t } = useTranslation();

    // Result context
    const {
        hoveredProfileIndex,
        setHoveredProfileIndex,
        elevationLegIndex,
        setElevationLegIndex
    } = useResult();

    // Controls visibility of the custom marker and fixed tooltip
    const [displayMarker, setDisplayMarker] = useState<boolean>(true);

    const ascent = polyInfo?.totalAscent;
    const descent = polyInfo?.totalDescent;
    const profile = polyInfo?.elevationProfile;

    // Do not render component if elevation data are missing
    if (!profile || ascent === undefined || descent === undefined) {
        return null;
    }

    // Convert elevation profile into ApexCharts format
    const seriesData = profile.map(p => ({
        x: p.distance / 1000,
        y: p.elevation
    }));

    const series = [
        {
            name: "Elevation",
            data: seriesData
        }
    ];

    // Calculate min and max elevation to configure Y axis
    const elevations = profile.map(p => p.elevation);
    const minElev = Math.min(...elevations);
    const maxElev = Math.max(...elevations);

    const range = maxElev - minElev;

    // Dynamic Y axis step
    let step = Math.ceil(range / 6);
    step = Math.max(step, 60);

    // Determine currently hovered point in the profile
    const hoveredPoint =
    elevationLegIndex === legIndex &&
    hoveredProfileIndex !== null &&
    hoveredProfileIndex >= 0 &&
    hoveredProfileIndex < profile.length
        ? profile[hoveredProfileIndex]
        : null;

    const options: ApexCharts.ApexOptions = {
        chart: {
            type: "area",
            height: 220,

            // Disable zoom
            zoom: {
                enabled: false
            },

            // Hide default toolbar
            toolbar: {
                show: false
            },

            events: {
                // Triggered when mouse moves over chart
                mouseMove: (event, chartContext, config) => {
                    const idx = config.dataPointIndex;
                    // Hide fixed marker while hovering directly over chart
                    setDisplayMarker(false);
                    if (idx !== -1) {
                        setHoveredProfileIndex(idx);
                        setElevationLegIndex(legIndex);
                    }
                },
                // Reset hover state when leaving chart
                mouseLeave: () => {
                    setDisplayMarker(true);
                    setHoveredProfileIndex(null);
                    setElevationLegIndex(null);
                }
            }
        },

        stroke: {
            curve: "straight",
            width: 2
        },

        colors: ["var(--color-info)"],

        fill: {
            type: "gradient",
            gradient: {
                shadeIntensity: 0.2,
                opacityFrom: 0.8,
                opacityTo: 0.25
            }
        },

        dataLabels: {
            enabled: false
        },

        // Distance axis in km
        xaxis: {
            labels: {
                formatter: (v: number) => `${v.toFixed(1)} km`
            },
            tooltip: {
                enabled: false
            }
        },

        // Elevation axis in meters
        yaxis: {
            min: Math.floor(minElev / step) * step,
            max: Math.ceil(maxElev / step) * step,
            stepSize: step,
            labels: {
                formatter: (v: number) => `${Math.round(v)} m`
            },
        },

        // Custom tooltip displayed when hovering chart
        tooltip: {
            enabled: true,
            custom: ({ series, seriesIndex, dataPointIndex, w }) => {
                const x = w.globals.seriesX[seriesIndex][dataPointIndex];
                const y = series[seriesIndex][dataPointIndex];

                return `
                    <div class="elevation-tooltip">
                        <div>${x.toFixed(2)} km</div>
                        <div>${Math.round(y)} m</div>
                    </div>
                `;
            }
        },

        grid: {
            strokeDashArray: 2,
            padding: {
                left: 10
            }
        },

        // Custom marker that highlights the hovered point
        markers: {
            size: 0,
            strokeWidth: 2,
            discrete: displayMarker && hoveredProfileIndex !== null && elevationLegIndex === legIndex
                ? [
                    {
                        seriesIndex: 0,
                        dataPointIndex: hoveredProfileIndex,
                        size: 6,
                        fillColor: "var(--color-info)",
                        strokeColor: "white"
                    }
                ]
                : []
        }
    };

    return (
        <>
            {/* Elevation visibility toggle */}
            <div 
                onClick={() => openElevation(!polyInfo.elevationOpen)}
                className="elevation-profile"
            >
                <CustomTooltip title={polyInfo.elevationOpen ? t("tooltips.detail.publicTransport.closeElevationProfile") : t("tooltips.detail.publicTransport.elevationProfile")}>
                    <KeyboardArrowDownIcon className={polyInfo.elevationOpen ? "" : "rotate90"}/>
                </CustomTooltip>

                <LandscapeIcon
                    className="elevation-profile-icon"
                    sx={{ fontSize: 25 }}
                />
                {t("detailInfo.publicTransport.elevation")}
            </div>
            <div>
                {polyInfo.elevationOpen && (
                    <>
                        {/* Total ascent and descent summary */}
                        <div className="asc-desc">
                            <div className="asc-desc-divs">
                                <NorthEastIcon sx={{fontSize: 20}} /> {Math.round(ascent)} m
                            </div>
                            <div className="asc-desc-divs">
                                <SouthEastIcon sx={{fontSize: 20}} /> {Math.round(descent ?? 0)} m
                            </div>
                        </div>

                        {/* Elevation chart */}
                        <div style={{ width: "calc(100% - 20px)", height: 200, position: "relative" }}>
                            <ReactApexChart
                                options={options}
                                series={series}
                                type="area"
                                height={200}
                            />

                            {/* Fixed tooltip displayed when hovering profile from map */}
                            {hoveredPoint && displayMarker &&  (
                                <div className="elevation-fixed-tooltip">
                                    <div>
                                        {(hoveredPoint.distance / 1000).toFixed(2)} km&nbsp;•&nbsp;
                                    </div>
                                    <div>
                                        {Math.round(hoveredPoint.elevation)} m
                                    </div>
                                </div>
                            )}
                        </div>
                    </>
                )}
            </div>
        </>
    );
}

/** End of file ElevationProfile.tsx */
