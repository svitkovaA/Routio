/**
 * @file ModePreferences.tsx
 * @brief Component for configuring transport mode preferences
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from 'react';
import KeyboardArrowLeftIcon from '@mui/icons-material/KeyboardArrowLeft';
import Section from './Section/Section';
import "./ModePreferences.css";

type ModePreferencesProps = {
    title: string;                                                      // Section title
    speedLabel: string;                                                 // Label for average speed
    speed: number;                                                      // Average speed value 
    setSpeed: (value: number | ((prev: number) => number)) => void;     // Setter for average speed value
    speedBounds: { min: number, max: number };                          // Bounds for speed value
    distanceLabel: string;                                              // Label for max distance
    distance: number;                                                   // Max distance
    setDistance: (value: number | ((prev: number) => number)) => void;  // Setter for max distance
    distanceBounds: { min: number, max: number };                       // Bounds for max distance
    lockLabel?: string | null;                                          // Label for lock time
    lockTime?: number;                                                  // Lock time
    setLockTime?: (value: number | ((prev: number) => number)) => void; // Setter for lock time
    lockBounds?: { min: number, max: number };                          // Bounds for lock time
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
    // State controlling section expansion 
    const [isOpen, setIsOpen] = useState<boolean>(false);
    
    return (
        <div className={"settings-section " + (isOpen ? "opened" : "")}>
            {/* Section toggle */}
            <div className="toggle-settings" onClick={() => setIsOpen(!isOpen)}>
                <span>{title}</span>
                <KeyboardArrowLeftIcon fontSize="large" className={isOpen ? "rotate90" : ""} />
            </div>
            <div className={isOpen ? "settings-content" : "settings-content hidden"}>
                <div className="preferences">

                    {/* Maximum distance preference */}
                    <Section
                        label={distanceLabel}
                        value={distance}
                        setValue={setDistance}
                        bounds={distanceBounds}
                    />

                    {/* Average speed preference */}
                    <Section
                        label={speedLabel}
                        value={speed}
                        setValue={setSpeed}
                        bounds={speedBounds}
                    />

                    {/* Lock time preference */}
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
