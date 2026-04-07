/**
 * @file VerticalTimeLineHandle.tsx
 * @brief Custom hook that updates vertical timeline segment length based on element height
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect } from "react";
import type { RefObject } from "react";
import type { Leg, VerticalTimeline } from "../../../../types/types";

export function useVerticalTimeLineHandle(
    ref: RefObject<HTMLDivElement | null>,  // Reference to the element representing leg detail
    leg: Leg,                               // Leg associated with the timeline segment
    setVerticalTimeline: (value: VerticalTimeline[] | ((prev: VerticalTimeline[]) => VerticalTimeline[])) => void,  // Setter used to update vertical timeline segments
    index: number,                          // Index of the timeline segment corresponding to the leg
    offset: number = 0                      // Optional height offset
) {
    useEffect(() => {
        if (!ref.current) {
            return;
        }

        // Observe size changes of the referenced element
        const observer = new ResizeObserver((entries) => {
            for (const entry of entries) {
                const newLength = entry.contentRect.height + offset;

                // New timeline segment length based on element height
                setVerticalTimeline(prev => {
                    const copy = [...prev];

                    // Update length of the corresponding segment
                    if (copy[index]) {
                        copy[index] = { ...copy[index], length: newLength };
                    }
                    return copy;
                });
            }
        });

        // Start observing the element
        observer.observe(ref.current);

        return () => observer.disconnect();
    }, [leg, index, ref, offset, setVerticalTimeline]);
}

/** End of file VerticalTimelineHandle.tsx */
