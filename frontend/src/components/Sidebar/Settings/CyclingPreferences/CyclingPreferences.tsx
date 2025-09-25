/**
 * @file CyclingPreferences.tsx
 * @brief Displays cycling preferences in the settings
 * @author Andrea Svitkova (xsvitka00)
 */

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faAngleLeft, faMinus, faPlus } from '@fortawesome/free-solid-svg-icons';
import { TextField, InputAdornment, IconButton } from "@mui/material";
import { useTranslation } from "react-i18next";

type CyclingPreferencesProps = {
    isCyclingOpen: boolean;
    setIsCyclingOpen: (isOpen: boolean) => void;
    maxBikeDistance: number;
    setMaxBikeDistance: (value: number | ((prev: number) => number)) => void;
    bikeAverageSpeed: number;
    setBikeAverageSpeed: (value: number | ((prev: number) => number)) => void;
    bikeLockTime: number;
    setBikeLockTime: (value: number | ((prev: number) => number)) => void;
    className?: string;
};

function CyclingPreferences({ 
    isCyclingOpen, 
    setIsCyclingOpen,
    maxBikeDistance,
    setMaxBikeDistance,
    bikeAverageSpeed,
    setBikeAverageSpeed,
    bikeLockTime,
    setBikeLockTime,
    className
}: CyclingPreferencesProps) {
    const { t } = useTranslation();

    const handleChangeSpeed = (e: React.ChangeEvent<HTMLInputElement>) => {
        setBikeAverageSpeed(Number(e.target.value));
    };

    const handleLockTimeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setBikeLockTime(Number(e.target.value))
    }

    const handleChangeDistance = (e: React.ChangeEvent<HTMLInputElement>) => {
        setMaxBikeDistance(Number(e.target.value));
    };

    return (
        <div className={"settings-section " + className}>
            <div className="toggle-settings" onClick={() => setIsCyclingOpen(!isCyclingOpen)}>
                <span>{t("settingsTab.cyclingPreferences")}</span>
                <FontAwesomeIcon icon={faAngleLeft} className={isCyclingOpen ? "rotate90" : ""}/>
            </div>
            <div className={isCyclingOpen ? "settings-content" : "settings-content hidden"}>
                <div className="preferences">
                    <div className="section">
                        <span className="section-label">
                            {t("settingsTab.walkingPreferencesTab.maxWalkingDistance")}
                        </span>
                        <TextField
                            type="number"
                            value={maxBikeDistance}
                            onChange={handleChangeDistance}
                            className="number-input"
                            InputProps={{
                                inputProps: { min: 0, max: 10, step: 1 },
                                endAdornment: (
                                <InputAdornment position="end" style={{ display: 'flex', gap: '4px' }}>
                                    <IconButton onClick={() => setMaxBikeDistance(prev => Math.max(0, prev - 1))} size="small">
                                        <FontAwesomeIcon className="fa-icon" icon={faMinus} />
                                    </IconButton>
                                    <IconButton onClick={() => setMaxBikeDistance(prev => Math.min(10, prev + 1))} size="small">
                                        <FontAwesomeIcon className="fa-icon" icon={faPlus} />
                                    </IconButton>
                                </InputAdornment>
                                )
                            }}
                        />
                    </div>

                    <div className="section">
                        <span className="section-label">
                            {t("settingsTab.walkingPreferencesTab.averageWalkingSpeed")}
                        </span>
                        <TextField
                            type="number"
                            value={bikeAverageSpeed}
                            onChange={handleChangeSpeed}
                            className="number-input"
                            InputProps={{
                                inputProps: { min: 5, max: 40, step: 1 }
                            }}
                        />
                    </div>
                    <div className="section">
                        <span className="section-label">
                            Time to lock bike
                        </span>
                        <TextField
                            type="number"
                            value={bikeLockTime}
                            onChange={handleLockTimeChange}
                            className="number-input"
                            InputProps={{
                                inputProps: { min: 1, max: 20, step: 1 }
                            }}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}

export default CyclingPreferences;

/** End of file CyclingPreferences.tsx */
