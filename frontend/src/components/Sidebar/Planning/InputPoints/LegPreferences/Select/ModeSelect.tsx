/**
 * @file ModeSelect.tsx
 * @brief Component for selecting transport mode preference for a route leg
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import { Mode } from "../../../../../types/types";
import { modeIcons } from "../../../Icons/Icons";
import { useInput } from "../../../../../InputContext";
import CustomTooltip from "../../../../../CustomTooltip/CustomTooltip";
import "./Select.css";

type ModeSelectProps = {
    index: number;          // Index of the leg in legPreferences array
}

function ModeSelect({ index }: ModeSelectProps) {
    // Translation function
    const { t } = useTranslation();

    // User input preference
    const {
        legPreferences, setLegPreferences
    } = useInput();

    // Controls visibility of dropdown menu
    const [open, setOpen] = useState<boolean>(false);

    /**
     * Updates selected transport mode for current leg
     * 
     * @param value Selected transport mode
     */
    const handleSelect = (value: Mode) => {
        setLegPreferences((prev) => {
            const newLegPreferences = [...prev];
            newLegPreferences[index] = { ...newLegPreferences[index], mode: value};
            
            return newLegPreferences;
        });
    }

    return (
        <div className="select">
            <CustomTooltip title={t("tooltips.inputForm.modePreferences")}>
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
                        <KeyboardArrowDownIcon 
                            className={open ? "rotate" : ""}
                            sx={{ color: 'var(--color-icons)' }}
                        />
                    </span>
                </button>
            </CustomTooltip>

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
