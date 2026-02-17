/**
 * @file ModePreferences.tsx
 * @brief Component for configuring transport mode preferences
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import KeyboardArrowLeftIcon from '@mui/icons-material/KeyboardArrowLeft';
import Section from './Section/Section';
import "./ModePreferences.css";

type ModePreferencesProps = {
    title: string;                                                      // Section title
    speed: number;                                                      // Average speed value 
    setSpeed: (value: number | ((prev: number) => number)) => void;     // Setter for average speed value
    speedBounds: { min: number, max: number };                          // Bounds for speed value
    distance: number;                                                   // Max distance
    setDistance: (value: number | ((prev: number) => number)) => void;  // Setter for max distance
    distanceBounds: { min: number, max: number };                       // Bounds for max distance
    lockTime?: number;                                                  // Lock time
    setLockTime?: (value: number | ((prev: number) => number)) => void; // Setter for lock time
    lockBounds?: { min: number, max: number };                          // Bounds for lock time
};

function ModePreferences({ 
    title,
    speed,
    setSpeed,
    speedBounds,
    distance,
    setDistance,
    distanceBounds,
    lockTime,
    setLockTime,
    lockBounds
}: ModePreferencesProps) {
    // Translation function
    const { t } = useTranslation();

    // State controlling section expansion 
    const [isOpen, setIsOpen] = useState<boolean>(false);
    
    return (
        <div className={"settings-section " + (isOpen ? "opened" : "")}>
            {/* Section toggle */}
            <div className="toggle-settings" onClick={() => setIsOpen(!isOpen)}>
                <span>{title}</span>
                <KeyboardArrowLeftIcon 
                    fontSize="large" 
                    className={isOpen ? "rotate90" : ""} 
                    sx={{ color: 'var(--color-text-primary)' }}
                />
            </div>
            <div className={isOpen ? "settings-content" : "settings-content hidden"}>
                <div className="preferences">

                    {/* Maximum distance preference */}
                    <Section
                        label={t("settingsTab.preferencesTab.maxDistance")}
                        value={distance}
                        setValue={setDistance}
                        bounds={distanceBounds}
                    />

                    {/* Average speed preference */}
                    <Section
                        label={t("settingsTab.preferencesTab.averageSpeed")}
                        value={speed}
                        setValue={setSpeed}
                        bounds={speedBounds}
                    />

                    {/* Lock time preference */}
                    {lockTime !== undefined && setLockTime && lockBounds && (
                        <Section
                            label={t("settingsTab.preferencesTab.lockTime")}
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
