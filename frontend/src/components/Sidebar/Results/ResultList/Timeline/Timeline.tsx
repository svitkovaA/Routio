/**
 * @file Timeline.tsx
 * @brief Displays a horizontal timeline
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useRef, useState } from "react";
import { Leg } from "../../../../types/types";
import { timelineIcons } from "../../../Planning/Icons/Icons";
import "./Timeline.css"

type TimelineProps = {
    totalDuration: number;
    legs: Leg[];
}

function Timeline({
    totalDuration,
    legs
} : TimelineProps) {
    const timelineRef = useRef<HTMLDivElement>(null);
    const [width, setWidth] = useState(0);

    useEffect(() => {
        if (!timelineRef.current) return;

        const observer = new ResizeObserver((entries) => {
            for (let entry of entries) {
                setWidth(entry.contentRect.width);
            }
        });

        observer.observe(timelineRef.current);

        return () => observer.disconnect();
    }, []);

    return (
        <div
            ref={timelineRef}
            className="timeline"
        >
            {legs.map((leg) => {
                const legWidth = leg.duration / totalDuration * width;
                const left = leg.accumulatedDuration / totalDuration * width;

                return (
                    <div 
                        className="timeline-leg"
                        style={{
                            left: left,
                            width: legWidth,
                            borderColor: leg.color,
                            borderStyle: leg.mode === "foot" || leg.mode === "bicycle" ? "dashed" : "solid",
                        }}
                    >
                        {timelineIcons[leg.mode]}
                    </div>
                );
            })}
        </div>
    );
}

export default Timeline;

/** End of file Timeline.tsx */
