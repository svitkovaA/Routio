/**
 * @file Settings.tsx
 * @brief Display settings sidebar component
 * @author Andrea Svitkova (xsvitka00)
 */

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faAngleLeft } from '@fortawesome/free-solid-svg-icons';
import { useTranslation } from "react-i18next";
import TransportPreferences from "./TransportPreferences/TransportPreferences";
import ModePreferences from "./ModePreferences/ModePreferences";
import { useSettings } from "../../SettingsContext";
import "./Settings.css";

type SettingsProps = {
    closeSettings: () => void;
};

function Settings({ closeSettings } : SettingsProps) {
    const { t } = useTranslation();
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
        <div className="sidebar-header">
            <button className="back-button" onClick={closeSettings}  >
                <FontAwesomeIcon icon={faAngleLeft} />
            </button>
            <span onClick={closeSettings}>{t("settings")}</span>
        </div>

        <div className="sidebar-content">
            <TransportPreferences />

            <ModePreferences 
                title={t("settingsTab.cyclingPreferences")}
                speedLabel={t("settingsTab.cyclingPreferencesTab.averageCyclingSpeed")}
                speed={bikeAverageSpeed}
                setSpeed={setBikeAverageSpeed}
                speedBounds={{ min: 5, max: 40 }}
                distanceLabel={t("settingsTab.cyclingPreferencesTab.maxCyclingDistance")}
                distance={maxBikeDistance}
                setDistance={setMaxBikeDistance}
                distanceBounds={{ min: 0, max: 100}}
                lockLabel={t("settingsTab.cyclingPreferencesTab.cyclingLockTime")}
                lockTime={bikeLockTime}
                setLockTime={setBikeLockTime}
                lockBounds={{ min: 0, max: 10 }}
            />

            <ModePreferences 
                title={t("settingsTab.bikesharingPreferences")}
                speedLabel={t("settingsTab.bikesharingPreferencesTab.averageBikesharingSpeed")}
                speed={bikesharingAverageSpeed}
                setSpeed={setBikesharingAverageSpeed}
                speedBounds={{ min: 5, max: 30 }}
                distanceLabel={t("settingsTab.bikesharingPreferencesTab.maxBikesharingDistance")}
                distance={maxBikesharingDistance}
                setDistance={setMaxBikesharingDistance}
                distanceBounds={{ min: 0, max: 30}}
                lockLabel={t("settingsTab.bikesharingPreferencesTab.bikesharingLockTime")}
                lockTime={bikesharingLockTime}
                setLockTime={setBikesharingLockTime}
                lockBounds={{ min: 0, max: 15 }}
            />

            <ModePreferences 
                title={t("settingsTab.walkingPreferences")}
                speedLabel={t("settingsTab.walkingPreferencesTab.averageWalkingSpeed")}
                speed={walkAverageSpeed}
                setSpeed={setWalkAverageSpeed}
                speedBounds={{ min: 2, max: 15 }}
                distanceLabel={t("settingsTab.walkingPreferencesTab.maxWalkingDistance")}
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
