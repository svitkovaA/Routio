/**
 * @file LegPreferences.tsx
 * @brief Component for editing leg preferences
 */

import { useTranslation } from "react-i18next";
import ClickAwayListener from "@mui/material/ClickAwayListener";
import KeyboardArrowLeftIcon from '@mui/icons-material/KeyboardArrowLeft';
import { modeIcons } from "../../Icons/IconMappings";
import ModeSelect from "./Select/ModeSelect";
import { useInput } from "../../../../Contexts/InputContext";
import CustomTooltip from "../../../../CustomTooltip/CustomTooltip";
import "./LegPreferences.css";

type LegPreferencesProps = {
    render: boolean;        // Determines whether the component should be rendered
    index: number;          // Index of the leg in legPreferences array
}

function LegPreferences({
    render,
    index
}: LegPreferencesProps) {
    // Translation function
    const { t } = useTranslation();

    // User input context
    const { legPreferences, setLegPreferences } = useInput();

    /**
     * Updates state of the preference panel for the specific leg
     * 
     * @param value True, open panel, false close panel
     */
    const setLegPreference = (value: boolean) => {
        setLegPreferences((prev) => {
            const newLegPreferences = [...prev];
            if (!newLegPreferences[index].fixed) {
                newLegPreferences[index] = { ...newLegPreferences[index], open: value};
            }
            
            return newLegPreferences;
        })
    };

    // Do not render component if disabled
    if (!render) {
        return null;
    }

    return (
        <div className="leg-preferences-wrapper">
            {!legPreferences[index].open ? (
                <CustomTooltip title={legPreferences[index].fixed ? t("tooltips.inputForm.blockedPreferences") : t("tooltips.inputForm.modePreferences")}>
                    <div
                        className={
                            "leg-preferences-button " + 
                            (legPreferences[index].mode === "multimodal" ? "multimodal " : "") +
                            (legPreferences[index].fixed ? "fixed" : "")
                        }
                        onClick={() => setLegPreference(true)}
                    >
                        {modeIcons.map((mode) => 
                            mode.value === legPreferences[index].mode ? mode.html : null
                        )}
                    </div>
                </CustomTooltip>
            ) : (
                <ClickAwayListener
                    mouseEvent="onMouseDown"
                    touchEvent="onTouchStart"
                    onClickAway={() => {
                        setTimeout(() => {
                            setLegPreference(false);
                        }, 100);
                    }}
                >
                    <div className="leg-preferences-select-wrapper">
                        <div className="select-wrapper">
                            <ModeSelect
                                index={index}
                            />
                        </div>
                        <CustomTooltip title={t("tooltips.inputForm.closeLegPrefs")}>
                            <KeyboardArrowLeftIcon 
                                onClick={() => setLegPreference(false)}
                                sx={{ color: 'var(--color-icons)' }}
                            />
                        </CustomTooltip>
                    </div>
                </ClickAwayListener>
            )}
        </div>
    );
}

export default LegPreferences;

/** End of file LegPreferences.tsx */
