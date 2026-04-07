/**
 * @file VerticalTimelineComponent.tsx
 * @brief Renders the vertical timeline for trip legs
 * @author Andrea Svitkova (xsvitka00)
 */

import type { VerticalTimeline } from "../../../../types/types";
import "./VerticalTimelineComponent.css";

type VerticalTimelineComponentProps = {
    verticalTimeline: VerticalTimeline[];   // Array of timeline segments corresponding to trip legs
}

function VerticalTimelineComponent({ verticalTimeline } : VerticalTimelineComponentProps) {
    // Filter out waiting and artificial segments
    const nonWaitLegs = verticalTimeline.filter((i) => i.mode !== "wait" && !i.artificial);
    
    return (
        <div className="vertical-timeline">
            {nonWaitLegs.map((item, index) => (
                <div
                    key={`${index}`}
                    className="vertical-timeline-item"
                    style={{
                        borderColor: item.color,
                        height: item.length,
                        borderStyle: (item.mode === "foot" || item.mode === "bicycle" || item.mode === "transfer") ? 'dashed' : 'solid'
                    }}
                >
                    <div className="timeline-dot" />
                    {index === nonWaitLegs.length - 1 && <div className="timeline-dot last"/>}
                </div>
            ))}
        </div>
    );
}

export default VerticalTimelineComponent;

/** End of file VerticalTimelineComponent.tsx */
