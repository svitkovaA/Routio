/**
 * @file ModePreferences.tsx
 * @brief
 * @author Andrea Svitkova (xsvitka00)
 */

import KeyboardArrowLeftIcon from '@mui/icons-material/KeyboardArrowLeft';
import Section from './Section/Section';
import "./ModePreferences.css";
import { useState } from 'react';

type ModePreferencesProps = {
    title: string;
    speedLabel: string;
    speed: number;
    setSpeed: (value: number | ((prev: number) => number)) => void;
    speedBounds: { min: number, max: number };
    distanceLabel: string;
    distance: number;
    setDistance: (value: number | ((prev: number) => number)) => void;
    distanceBounds: { min: number, max: number };
    lockLabel?: string | null;
    lockTime?: number;
    setLockTime?: (value: number | ((prev: number) => number)) => void;
    lockBounds?: { min: number, max: number };
};

function ModePreferences({ 
    title,
    speedLabel,
    speed,
    setSpeed,
    speedBounds,
    distanceLabel,
    distance,
    setDistance,
    distanceBounds,
    lockLabel,
    lockTime,
    setLockTime,
    lockBounds
}: ModePreferencesProps) {
    const [isOpen, setIsOpen] = useState<boolean>(false);
    
    return (
        <div className={"settings-section " + (isOpen ? "opened" : "")}>
            <div className="toggle-settings" onClick={() => setIsOpen(!isOpen)}>
                <span>{title}</span>
                <KeyboardArrowLeftIcon fontSize="large" className={isOpen ? "rotate90" : ""} />
            </div>
            <div className={isOpen ? "settings-content" : "settings-content hidden"}>
                <div className="preferences">
                    <Section
                        label={distanceLabel}
                        value={distance}
                        setValue={setDistance}
                        bounds={distanceBounds}
                    />
                    <Section
                        label={speedLabel}
                        value={speed}
                        setValue={setSpeed}
                        bounds={speedBounds}
                    />
                    {lockLabel && lockTime && setLockTime && lockBounds && (
                        <Section
                            label={lockLabel}
                            value={lockTime}
                            setValue={setLockTime}
                            bounds={lockBounds}
                        />
                    )}
                </div>
            </div>
        </div>
    );
}

export default ModePreferences;

/** End of file ModePreferences.tsx */
