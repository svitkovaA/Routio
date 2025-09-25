/**
 * @file BikesharingPreferences.tsx
 * @brief Displays bikesharing preferences in the settings
 * @author Andrea Svitkova (xsvitka00)
 */

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faAngleLeft, faMinus, faPlus } from '@fortawesome/free-solid-svg-icons';
import { TextField, InputAdornment, IconButton } from "@mui/material";
import { useTranslation } from "react-i18next";

type BikesharingPreferencesProps = {
    isBikesharingOpen: boolean;
    setIsBikesharingOpen: (isOpen: boolean) => void;
    maxBikesharingDistance: number;
    setMaxBikesharingDistance: (value: number | ((prev: number) => number)) => void;
    bikesharingAverageSpeed: number;
    setBikesharingAverageSpeed: (value: number | ((prev: number) => number)) => void;
    bikesharingLockTime: number;
    setBikesharingLockTime: (value: number | ((prev: number) => number)) => void;
    className?: string;
};

function BikesharingPreferences({ 
    isBikesharingOpen,
    setIsBikesharingOpen,
    maxBikesharingDistance,
    setMaxBikesharingDistance,
    bikesharingAverageSpeed,
    setBikesharingAverageSpeed,
    bikesharingLockTime,
    setBikesharingLockTime,
    className
}: BikesharingPreferencesProps) {
    const { t } = useTranslation();

    const handleChangeSpeed = (e: React.ChangeEvent<HTMLInputElement>) => {
        setBikesharingAverageSpeed(Number(e.target.value));
    };

    const handleLockTimeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setBikesharingLockTime(Number(e.target.value))
    }

    const handleChangeDistance = (e: React.ChangeEvent<HTMLInputElement>) => {
        setMaxBikesharingDistance(Number(e.target.value));
    };

    return (
        <div className={"settings-section " + className}>
            <div className="toggle-settings" onClick={() => setIsBikesharingOpen(!isBikesharingOpen)}>
                <span>Bikesharing preferences</span>
                <FontAwesomeIcon icon={faAngleLeft} className={isBikesharingOpen ? "rotate90" : ""}/>
            </div>
            <div className={isBikesharingOpen ? "settings-content" : "settings-content hidden"}>
                <div className="preferences">
                    <div className="section">
                        <span className="section-label">
                            {t("settingsTab.walkingPreferencesTab.maxWalkingDistance")}
                        </span>
                        <TextField
                            type="number"
                            value={maxBikesharingDistance}
                            onChange={handleChangeDistance}
                            className="number-input"
                            InputProps={{
                                inputProps: { min: 0, max: 10, step: 1 },
                                endAdornment: (
                                <InputAdornment position="end" style={{ display: 'flex', gap: '4px' }}>
                                    <IconButton onClick={() => setMaxBikesharingDistance(prev => Math.max(0, prev - 1))} size="small">
                                        <FontAwesomeIcon className="fa-icon" icon={faMinus} />
                                    </IconButton>
                                    <IconButton onClick={() => setMaxBikesharingDistance(prev => Math.min(10, prev + 1))} size="small">
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
                            value={bikesharingAverageSpeed}
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
                            value={bikesharingLockTime}
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

export default BikesharingPreferences;

/** End of file BikesharingPreferences.tsx */
