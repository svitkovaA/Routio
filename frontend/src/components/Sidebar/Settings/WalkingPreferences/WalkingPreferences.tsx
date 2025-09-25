/**
 * @file WalkingPreferences.tsx
 * @brief Displays walking preferences in the settings
 * @author Andrea Svitkova (xsvitka00)
 */

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faAngleLeft } from '@fortawesome/free-solid-svg-icons';
import { faPlus, faMinus } from '@fortawesome/free-solid-svg-icons';
import { IconButton, TextField, InputAdornment } from "@mui/material";
import { useTranslation } from "react-i18next";
import './WalkingPreferences.css'

type WalkingSettingsProps = {
    isWalkingOpen: boolean;
    setIsWalkingOpen: (isOpen: boolean) => void;
    maxWalkDistance: number;
    setMaxWalkDistance: (value: number | ((prev: number) => number)) => void;
    walkAverageSpeed: number;
    setWalkAverageSpeed: (value: number | ((prev: number) => number)) => void;
    className?: string;
};

function WalkingSettings({ 
    isWalkingOpen, 
    setIsWalkingOpen,
    maxWalkDistance,
    setMaxWalkDistance,
    walkAverageSpeed,
    setWalkAverageSpeed,
    className
}: WalkingSettingsProps) {
    const { t } = useTranslation();

    const handleChangeDistance = (e: React.ChangeEvent<HTMLInputElement>) => {
        setMaxWalkDistance(Number(e.target.value));
    };

    const handleChangeSpeed = (e: React.ChangeEvent<HTMLInputElement>) => {
        setWalkAverageSpeed(Number(e.target.value));
    };
    return (
        <div className={"settings-section " + className}>
            <div className="toggle-settings" onClick={() => setIsWalkingOpen(!isWalkingOpen)}>
                <span>{t("settingsTab.walkingPreferences")}</span>
                <FontAwesomeIcon icon={faAngleLeft} className={isWalkingOpen ? "rotate90" : ""}/>
            </div>
            <div className={isWalkingOpen ? "settings-content" : "settings-content hidden"}>
                <div className="preferences">
                    <div className="section">
                        <span className="section-label">
                            {t("settingsTab.walkingPreferencesTab.maxWalkingDistance")}
                        </span>
                        <TextField
                            type="number"
                            value={maxWalkDistance}
                            onChange={handleChangeDistance}
                            className="number-input"
                            InputProps={{
                                inputProps: { min: 0, max: 10, step: 1 },
                                endAdornment: (
                                <InputAdornment position="end" style={{ display: 'flex', gap: '4px' }}>
                                    <IconButton onClick={() => setMaxWalkDistance(prev => Math.max(0, prev - 1))} size="small">
                                        <FontAwesomeIcon className="fa-icon" icon={faMinus} />
                                    </IconButton>
                                    <IconButton onClick={() => setMaxWalkDistance(prev => Math.min(10, prev + 1))} size="small">
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
                            value={walkAverageSpeed}
                            onChange={handleChangeSpeed}
                            className="number-input"
                            InputProps={{
                                inputProps: { min: 0, max: 10, step: 1 },
                                endAdornment: (
                                <InputAdornment position="end" style={{ display: 'flex', gap: '4px' }}>
                                    <IconButton onClick={() => setWalkAverageSpeed(prev => Math.max(0, prev - 1))} size="small">
                                        <FontAwesomeIcon className="fa-icon" icon={faMinus} />
                                    </IconButton>
                                    <IconButton onClick={() => setWalkAverageSpeed(prev => Math.min(10, prev + 1))} size="small">
                                        <FontAwesomeIcon className="fa-icon" icon={faPlus} />
                                    </IconButton>
                                </InputAdornment>
                                )
                            }}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}

export default WalkingSettings;

/** End of file WalkingPreferences.tsx */
