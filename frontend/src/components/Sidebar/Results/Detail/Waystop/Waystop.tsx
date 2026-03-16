/**
 * @file Waystop.tsx
 * @brief Displays a stop in the trip detail
 * @author Andrea Svitkova (xsvitka00)
 */

import "./Waystop.css";

type WaystopProps = {
    time: string;                   // Time associated with the stop
    name: string | undefined;       // Name of the stop location
};

function Waystop({
    time,
    name
} : WaystopProps) {
    return (
        <div className="waystop">
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
