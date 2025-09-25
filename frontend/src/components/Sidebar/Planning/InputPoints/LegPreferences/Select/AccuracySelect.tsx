/**
 * @file AccuracySelect.tsx
 * @brief Dropdown component for selecting accuracy preference in leg preferences
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faAngleDown } from "@fortawesome/free-solid-svg-icons";
import { LegPreference } from "../../../../../types/types";
import { accuracyIcons } from "../../../Icons/Icons";

type AccuracySelectProps = {
    legPreferences: LegPreference[];
    setLegPreferences: (modes: LegPreference[] | ((prev: LegPreference[]) => LegPreference[])) => void;
    index: number;
}

function AccuracySelect({ 
    legPreferences, 
    setLegPreferences, 
    index 
}: AccuracySelectProps) {
    const [open, setOpen] = useState<boolean>(false);
    
    const handleSelect = (value: boolean) => {
        setLegPreferences((prev) => {
            const newLegPreferences = [...prev];
            newLegPreferences[index] = { ...newLegPreferences[index], exact: value};
            return newLegPreferences;
        });
    }
    
    return (
        <div className="select">
            <button
                onBlur={() => setOpen(false)}
                className={"controls-button accuracy-select " + (open ? "open" : "")}
                onClick={() => setOpen(!open)}
                type="button"
                tabIndex={-1}
            >
                {accuracyIcons.map((accuracy) => 
                    accuracy.exact === legPreferences[index].exact ? accuracy.html : null
                )}
                <span className="accuracy-arrow">
                    <FontAwesomeIcon icon={faAngleDown} className={open ? "rotate" : ""} />
                </span>
            </button>

            {open && (
                <div className="dropdown dropdown-accuracy">
                    {accuracyIcons.map((accuracy) => (
                        <div
                            className={"dropdown-item " + (accuracy.exact === legPreferences[index].exact ? "selected" : "")}
                            onMouseDown={() => handleSelect(accuracy.exact)}
                        >
                            {accuracy.html}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default AccuracySelect;

/** End of file AccuracySelect.tsx */
