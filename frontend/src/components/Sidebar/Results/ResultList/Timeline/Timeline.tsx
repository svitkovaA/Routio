/**
 * @file Timeline.tsx
 * @brief Displays a horizontal timeline representing trip legs
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useRef, useState } from "react";
import type { Leg } from "../../../../types/types";
import { timelineIcons } from "../../../Planning/Icons/IconMappings";
import "./Timeline.css"

type TimelineProps = {
    totalDuration: number;      // Total duration of the trip
    legs: Leg[];                // List of trip legs
}

function Timeline({
    totalDuration,
    legs
} : TimelineProps) {
    // Reference to the timeline container element
    const timelineRef = useRef<HTMLDivElement>(null);

    // Current width of the timeline container
    const [width, setWidth] = useState(0);

    /**
     * Observes timeline container size change
     */
    useEffect(() => {
        if (!timelineRef.current) {
            return;
        }

        // Create ResizeObserver to detect changes in container size
        const observer = new ResizeObserver((entries) => {
            for (const entry of entries) {
                // Update component state with the new container width
                setWidth(entry.contentRect.width);
            }
        });
        // Start observing the timeline container
        observer.observe(timelineRef.current);

        return () => observer.disconnect();
    }, []);

    return (
        <div
            ref={timelineRef}
            className="timeline"
        >
            {legs.map((leg, index) => {
                // Calculate width of the leg segment relative to the total trip duration
                const legWidth = leg.duration / totalDuration * width;

                // Calculate horizontal offset of the leg based on accumulated trip duration
                const left = leg.accumulatedDuration / totalDuration * width;

                return (
                    <div 
                        key={`${index}-${totalDuration}`}
                        className="timeline-leg"
                        style={{
                            left: left,
                            width: legWidth,
                            borderColor: leg.color,
                            borderStyle: leg.mode === "foot" || leg.mode === "bicycle" ? "dashed" : "solid",
                        }}
                    >
                        <div 
                            className="timeline-anchor"
                        >
                            {timelineIcons[leg.mode]}
                            {leg.line && (
                                <div 
                                    className="leg-public-code" 
                                    style={{ backgroundColor: leg.color }}
                                >
                                    {leg.line.publicCode}
                                </div>
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

export default Timeline;

/** End of file Timeline.tsx */
