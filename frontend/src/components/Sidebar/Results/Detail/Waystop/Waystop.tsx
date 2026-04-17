/**
 * @file Waystop.tsx
 * @brief Displays a stop in the trip detail
 * @author Andrea Svitkova (xsvitka00)
 */

import { useLayoutEffect, useRef } from "react";
import "./Waystop.css";

type WaystopProps = {
    time: string;                               // Time associated with the stop
    name: string | undefined;                   // Name of the stop location
    updateHeight?: (value: number) => void;     // Callback to update component height
};

function Waystop({
    time,
    name,
    updateHeight
} : WaystopProps) {
    const ref = useRef<HTMLDivElement>(null);

    /**
     * Observes element size changes
     */
    useLayoutEffect(() => {
        if (!ref.current) {
            return
        };

        const observer = new ResizeObserver(() => {
            if (!ref.current) return;

            // Get current height
            const height = ref.current.offsetHeight;
            updateHeight?.(height);
        });

        // Start observing element
        observer.observe(ref.current);

        return () => observer.disconnect();
    }, [updateHeight]);

    return (
        <div className="waystop" ref={ref} >
            <div className="waystop-detail">
                <span>
                    {time}
                </span>
                <span>
                    {name}
                </span>
            </div>
        </div>
    )
}

export default Waystop;

/** End of file Waystop.tsx */
