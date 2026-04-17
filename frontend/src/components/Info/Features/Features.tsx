/**
 * @file Features.tsx
 * @brief Component for displaying other information about the application
 * @author Andrea Svitkova (xsvitka00)
 */

import TimelineIcon from '@mui/icons-material/Timeline';
import ExploreIcon from '@mui/icons-material/Explore';
import StraightenIcon from '@mui/icons-material/Straighten';
import { useTranslation } from 'react-i18next';
import { Trans } from "react-i18next";
import "./Features.css"

function Features() {
    // Translation function
    const { t } = useTranslation();

    return(
        <div className="about-wrapper">
            <div className="about-section">
                <p className="about-header">
                    {t("info.stations.title")}
                </p>
                <div>
                    <Trans i18nKey="info.stations.desc" />
                    <ul className="features-list">
                        <li className="features-item">
                            <TimelineIcon className="features-icon" />

                            <div className="feature-content">
                                <strong className="feature-title">
                                    {t("info.stations.factors.availability.title")}
                                </strong>
                                <div>
                                    {t("info.stations.factors.availability.desc")}
                                </div>
                            </div>
                        </li>

                        <li className="features-item">
                            <ExploreIcon className="features-icon" />

                            <div className="feature-content">
                                <strong className="feature-title">
                                    {t("info.stations.factors.angle.title")}
                                </strong>
                                <div>
                                    {t("info.stations.factors.availability.desc")}
                                </div>
                            </div>
                        </li>

                        <li className="features-item">
                            <StraightenIcon className="features-icon" />

                            <div className="feature-content">
                                <strong className="feature-title">
                                    {t("info.stations.factors.distance.title")}
                                </strong>
                                <div>
                                    {t("info.stations.factors.distance.desc")}
                                </div>
                            </div>
                        </li>
                    </ul>
                <Trans i18nKey="info.stations.evaluation" />
                </div>
            </div>

            <div className="about-section">
                <p className="about-header">
                    {t("info.stations.predictionTitle")}
                </p>
                <p>
                    <Trans i18nKey="info.stations.predictionDesc" />
                </p>
            </div>

            <div className="about-section">
                <p className="about-header">
                    {t("info.stations.changeTitle")}
                </p>
                <p>
                    <Trans i18nKey="info.stations.changeDesc" />
                </p>
            </div>
        </div>
    );
}

export default Features;

/** End of file Features.tsx */
