/**
 * @file WaitDetail.tsx
 * @brief Displays the detail section for a wait leg
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useRef } from "react";
import { Leg, VerticalTimeline } from "../../../../types/types";

type WaitDetailProps = {
    leg: Leg;
    setVerticalTimeline: (value: VerticalTimeline[] | ((prev: VerticalTimeline[]) => VerticalTimeline[])) => void;
    index: number;
}

function WaitDetail({
    leg,
    setVerticalTimeline,
    index
} : WaitDetailProps) {
    const waitRef = useRef<HTMLDivElement>(null);
    
    useEffect(() => {
        if (!waitRef.current) return;

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

        observer.observe(waitRef.current);

        return () => observer.disconnect();
    }, [leg, index]);

    return (
        <div
            ref={waitRef}
        >
            wait
        </div>
    );
}
export default WaitDetail;

/** End of file WaitDetail.tsx */
