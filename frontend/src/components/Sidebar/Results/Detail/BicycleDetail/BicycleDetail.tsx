/**
 * @file BicycleDetail.tsx
 * @brief Displays the detail section for a bicycle leg
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useRef } from "react";
import { Leg, VerticalTimeline } from "../../../../types/types";

type BicycleDetailProps = {
    leg: Leg;
    setVerticalTimeline: (value: VerticalTimeline[] | ((prev: VerticalTimeline[]) => VerticalTimeline[])) => void;
    index: number;
}

function BicycleDetail({
    leg,
    setVerticalTimeline,
    index
} : BicycleDetailProps) {
    const bicycleRef = useRef<HTMLDivElement>(null);
    
    useEffect(() => {
        if (!bicycleRef.current) return;

        const observer = new ResizeObserver((entries) => {
            for (let entry of entries) {
                const newLength = entry.contentRect.height;

                setVerticalTimeline(prev => {
                    const copy = [...prev];
                    if (copy[index]) {
                        copy[index] = { ...copy[index], length: newLength };
                    }
                    return copy;
                });
            }
        });

        observer.observe(bicycleRef.current);

        return () => observer.disconnect();
    }, [leg, index]);

    return (
        <div
            ref={bicycleRef}
        >
            bike
        </div>
    );
}
export default BicycleDetail;

/** End of file BicycleDetail.tsx */
