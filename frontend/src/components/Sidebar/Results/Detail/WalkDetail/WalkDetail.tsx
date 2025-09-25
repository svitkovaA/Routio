/**
 * @file WalkDetail.tsx
 * @brief Displays the detail section for a walk leg
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useRef } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faRoute, faStopwatch } from "@fortawesome/free-solid-svg-icons";
import { Leg, VerticalTimeline } from "../../../../types/types";

type WalkDetailProps = {
    leg: Leg;
    setVerticalTimeline: (value: VerticalTimeline[] | ((prev: VerticalTimeline[]) => VerticalTimeline[])) => void;
    index: number;
}

function WalkDetail({
    leg,
    setVerticalTimeline,
    index
} : WalkDetailProps) {
    const walkDetailRef = useRef<HTMLDivElement>(null);
    
    useEffect(() => {
        if (!walkDetailRef.current) return;

        const observer = new ResizeObserver((entries) => {
            for (let entry of entries) {
                const newLength = entry.contentRect.height + 30;

                setVerticalTimeline(prev => {
                    const copy = [...prev];
                    if (copy[index]) {
                        copy[index] = { ...copy[index], length: newLength };
                    }
                    return copy;
                });
            }
        });

        observer.observe(walkDetailRef.current);
        return () => observer.disconnect();
    }, [leg, index]);

    return (
        <div
            ref={walkDetailRef}
        >
         <div>
            <FontAwesomeIcon icon={faStopwatch} />
            {(leg.duration / 60).toFixed(0)} min
            <FontAwesomeIcon icon={faRoute} />
            {(leg.distance / 1000).toFixed(1)} km
        </div>
        </div>
    );
}
export default WalkDetail;

/** End of file WalkDetail.tsx */
