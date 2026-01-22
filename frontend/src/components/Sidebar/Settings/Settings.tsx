/**
 * @file Settings.tsx
 * @brief Component for configuring routing and transport preferences
 * @author Andrea Svitkova (xsvitka00)
 */

import KeyboardArrowLeftIcon from '@mui/icons-material/KeyboardArrowLeft';
import { useTranslation } from "react-i18next";
import TransportPreferences from "./TransportPreferences/TransportPreferences";
import ModePreferences from "./ModePreferences/ModePreferences";
import { useSettings } from "../../SettingsContext";
import "./Settings.css";

type SettingsProps = {
    closeSettings: () => void;  // Callback used to close the settings view
};

function Settings({ closeSettings } : SettingsProps) {
    const { t } = useTranslation();

    // Settings context 
    const { 
        maxBikeDistance, setMaxBikeDistance,
        bikeAverageSpeed, setBikeAverageSpeed,
        bikeLockTime, setBikeLockTime,
        maxBikesharingDistance, setMaxBikesharingDistance,
        bikesharingAverageSpeed, setBikesharingAverageSpeed,
        bikesharingLockTime, setBikesharingLockTime,
        maxWalkDistance, setMaxWalkDistance,
        walkAverageSpeed, setWalkAverageSpeed
    } = useSettings();

    return (
    <div className="settings">
        {/* Sidebar header with back navigation */}
        <div className="sidebar-header">
            <button className="back-button" onClick={closeSettings}  >
                <KeyboardArrowLeftIcon 
                    fontSize="large"
                />
            </button>
            <span onClick={closeSettings}>{t("settings")}</span>
        </div>

        {/* Settings content */}
        <div className="sidebar-content">

            {/* Transport mode selection */}
            <TransportPreferences />

            {/* Cycling preferences */}
            <ModePreferences 
                title={t("settingsTab.cyclingPreferences")}
                speed={bikeAverageSpeed}
                setSpeed={setBikeAverageSpeed}
                speedBounds={{ min: 5, max: 40 }}
                distance={maxBikeDistance}
                setDistance={setMaxBikeDistance}
                distanceBounds={{ min: 0, max: 100}}
                lockTime={bikeLockTime}
                setLockTime={setBikeLockTime}
                lockBounds={{ min: 0, max: 10 }}
            />

            {/* Bikesharing preferences */}
            <ModePreferences 
                title={t("settingsTab.bikesharingPreferences")}
                speed={bikesharingAverageSpeed}
                setSpeed={setBikesharingAverageSpeed}
                speedBounds={{ min: 5, max: 30 }}
                distance={maxBikesharingDistance}
                setDistance={setMaxBikesharingDistance}
                distanceBounds={{ min: 0, max: 30}}
                lockTime={bikesharingLockTime}
                setLockTime={setBikesharingLockTime}
                lockBounds={{ min: 0, max: 15 }}
            />

            {/* Walking preferences */}
            <ModePreferences 
                title={t("settingsTab.walkingPreferences")}
                speed={walkAverageSpeed}
                setSpeed={setWalkAverageSpeed}
                speedBounds={{ min: 2, max: 15 }}
                distance={maxWalkDistance}
                setDistance={setMaxWalkDistance}
                distanceBounds={{ min: 0, max: 15}}
            />
        </div>
    </div>
    );
}

export default Settings;

/** End of file Settings.tsx */
