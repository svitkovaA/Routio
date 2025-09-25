/**
 * @file LegPreferences.tsx
 * @brief Displays component for editing trip prefferences, handles user interactions for opening and closing preferences with click-away behaviour
 * @author Andrea Svitkova (xsvitka00)
 */

import ClickAwayListener from "@mui/material/ClickAwayListener";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faAngleLeft } from "@fortawesome/free-solid-svg-icons";
import { LegPreference } from "../../../../types/types";
import { accuracyIcons, modeIcons } from "../../Icons/Icons";
import AccuracySelect from "./Select/AccuracySelect";
import ModeSelect from "./Select/ModeSelect";
import "./LegPreferences.css";

type LegPreferencesProps = {
    render: boolean;
    legPreferences: LegPreference[];
    setLegPreferences: (modes: LegPreference[] | ((prev: LegPreference[]) => LegPreference[])) => void;
    index: number;
}

function LegPreferences({
    render,
    legPreferences,
    setLegPreferences,
    index
}: LegPreferencesProps) {
    const setLegPreference = (value: boolean) => {
        setLegPreferences((prev) => {
            const newLegPreferences = [...prev];
            newLegPreferences[index] = { ...newLegPreferences[index], open: value};
            return newLegPreferences;
        })
    }

    if (!render) {
        return null;
    }

    return (
        <div className="leg-preferences-wrapper">
            {!legPreferences[index].open ? (
                <div
                    className={"leg-preferences-button " + (legPreferences[index].mode === "transit,bicycle,walk" ? "multimodal" : "")}
                    onClick={() => setLegPreference(true)}
                >
                    {modeIcons.map((mode) => 
                        mode.value === legPreferences[index].mode ? mode.html : null
                    )}
                    {accuracyIcons.map((accuracy) => 
                        accuracy.exact === legPreferences[index].exact ? accuracy.html : null
                    )}
                </div>
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
                <div className="preferences-wrapper">
                    <div className="select-wrapper">
                        <ModeSelect
                            legPreferences={legPreferences}
                            setLegPreferences={setLegPreferences}
                            index={index}
                        />
                        <AccuracySelect
                            legPreferences={legPreferences}
                            setLegPreferences={setLegPreferences}
                            index={index}
                        />
                    </div>
                    <FontAwesomeIcon icon={faAngleLeft} onClick={() => setLegPreference(false)}/>
                </div>
                </ClickAwayListener>
            )}
        </div>
    );
}

export default LegPreferences;

/** End of file LegPreferences.tsx */