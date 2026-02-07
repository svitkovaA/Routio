/**
 * @file VerticalTimelineComponent.tsx
 * @brief Renders the vertical timeline for trip legs
 * @author Andrea Svitkova (xsvitka00)
 */

import { VerticalTimeline } from "../../../../types/types";
import "./VerticalTimelineComponent.css";

type VerticalTimelineComponentProps = {
    verticalTimeline: VerticalTimeline[];
}

function VerticalTimelineComponent({ verticalTimeline } : VerticalTimelineComponentProps) {
    const nonWaitLegs = verticalTimeline.filter((i) => i.mode != "wait");
    return (
        <div className="vertical-timeline">
            {nonWaitLegs.map((item, index) => (
                <div
                    key={`${index}`}
                    className="vertical-timeline-item"
                    style={{
                        borderColor: item.color,
                        height: item.length,
                        borderStyle: (item.mode === "foot" || item.mode === "bicycle") ? 'dashed' : 'solid'
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
