import { RefObject, useEffect } from "react";
import { Leg, VerticalTimeline } from "../../../../types/types";

export function useVerticalTimeLineHandle(
    ref: RefObject<HTMLDivElement | null>,
    leg: Leg,
    setVerticalTimeline: (value: VerticalTimeline[] | ((prev: VerticalTimeline[]) => VerticalTimeline[])) => void,
    index: number,
    offset: number = 0
) {
    useEffect(() => {
        if (!ref.current) return;

        const observer = new ResizeObserver((entries) => {
            for (let entry of entries) {
                const newLength = entry.contentRect.height + offset;

                setVerticalTimeline(prev => {
                    const copy = [...prev];
                    if (copy[index]) {
                        copy[index] = { ...copy[index], length: newLength };
                    }
                    return copy;
                });
            }
        });

        observer.observe(ref.current);

        return () => observer.disconnect();
    }, [leg, index, ref, offset, setVerticalTimeline]);
}