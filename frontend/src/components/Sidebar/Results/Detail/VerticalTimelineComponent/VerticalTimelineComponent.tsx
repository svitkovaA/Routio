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

function VerticalTimelineComponent({ verticalTimeline }: VerticalTimelineComponentProps) {
    return (
        <div className="vertical-timeline">
            {verticalTimeline.map((item, index) => (
                <div
                    className="vertical-timeline-item"
                    style={{
                        borderColor: item.color,
                        height: item.length,
                        borderStyle: (item.mode === "foot" || item.mode === "bicycle") ? 'dashed' : 'solid'
                    }}
                >
                    <div className="timeline-dot" />
                    {index === verticalTimeline.length -1 && <div className="timeline-dot last"/>}
                </div>
            ))}
        </div>
    );
}

export default VerticalTimelineComponent;

/** End of file VerticalTimelineComponent.tsx */
