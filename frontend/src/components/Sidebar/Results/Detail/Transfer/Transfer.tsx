/**
 * @file Transfer.tsx
 * @brief Displays the transfer section between trip legs
 * @author Andrea Svitkova (xsvitka00)
 */

import { useEffect, useRef } from "react";
import { Leg, VerticalTimeline } from "../../../../types/types";

type TransferProps = {
    leg: Leg;
    setVerticalTimeline: (value: VerticalTimeline[] | ((prev: VerticalTimeline[]) => VerticalTimeline[])) => void;
    index: number;
}

function PublicTransportDetail({
    leg,
    setVerticalTimeline,
    index,
} : TransferProps) {
    const transferRef = useRef<HTMLDivElement>(null);
    
    useEffect(() => {
        if (!transferRef.current) return;

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

        observer.observe(transferRef.current);

        return () => observer.disconnect();
    }, [leg, index]);

    return (
        <div
            ref={transferRef}
        >
            transfer
        </div>
    );
}
export default PublicTransportDetail;

/** End of file Transfer.tsx */
