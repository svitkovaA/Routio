/**
 * @file ModeSelect.tsx
 * @brief Dropdown component for selecting mode preference in leg preferences
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faAngleDown } from "@fortawesome/free-solid-svg-icons";
import { Mode } from "../../../../../types/types";
import { modeIcons } from "../../../Icons/Icons";
import "./Select.css";
import { useInput } from "../../../../../InputContext";

type ModeSelectProps = {
    index: number;
}

function ModeSelect({ index }: ModeSelectProps) {
    const { legPreferences, setLegPreferences } = useInput();
    const [open, setOpen] = useState<boolean>(false);

    const handleSelect = (value: Mode) => {
        setLegPreferences((prev) => {
            const newLegPreferences = [...prev];
            newLegPreferences[index] = { ...newLegPreferences[index], mode: value};
            return newLegPreferences;
        });
    }

    return (
        <div className="select">
            <button
                onBlur={() => setOpen(false)}
                className={"controls-button mode " + (open ? "open" : "")}
                onClick={() => setOpen(!open)}
                type="button"
                tabIndex={-1}
            >
                {modeIcons.map((mode) => 
                    mode.value === legPreferences[index].mode ? mode.html : null
                )}
                <span className="mode-arrow">
                    <FontAwesomeIcon icon={faAngleDown} className={open ? "rotate" : ""} />
                </span>
            </button>

            {open && (
                <div className="dropdown dropdown-mode">
                    {modeIcons.map((mode) => (
                        <div
                            className={"dropdown-item " + (mode.value === legPreferences[index].mode ? "selected" : "")}
                            onMouseDown={() => handleSelect(mode.value)}
                        >
                            {mode.html}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default ModeSelect;

/** End of file ModeSelect.tsx */
