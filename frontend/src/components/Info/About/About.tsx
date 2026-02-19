/**
 * @file About.tsx
 * @brief Component for displaying general information abut the application
 * @author Andrea Svitkova (xsvitka00)
 */

import { useTranslation } from "react-i18next";
import { PUBLIC_URL } from "../../config/config";
import CustomTooltip from "../../CustomTooltip/CustomTooltip";
import "./About.css";

function About() {
    // Translation function
    const { t } = useTranslation();

    return (
        <div className="about-wrapper">

            {/* Application overview */}
            <div className="about-section">
                <p className="about-header">{t("info.overview.aboutTheApp")}</p>
                <p>
                    {t("info.overview.aboutTheAppSection")}
                </p>
            </div>

            {/* Supported transport modes */}
            <div className="about-section">
                <p className="about-header">{t("info.overview.supportedModes")}</p>
                <div className="about-transport-modes">
                    <CustomTooltip title={t("tooltips.info.bus")}>
                        <div>
                            <img className="data-brno" src={`${PUBLIC_URL}/img/publicTransport.svg`} alt="Data Brno logo" />
                        </div>
                    </CustomTooltip>

                    <CustomTooltip title={t("tooltips.info.foot")}>
                        <div>
                            <img className="data-brno" src={`${PUBLIC_URL}/img/foot.svg`} alt="Data Brno logo" />
                        </div>
                    </CustomTooltip>

                    <CustomTooltip title={t("tooltips.info.bicycle")}>
                        <div>
                            <img className="data-brno" src={`${PUBLIC_URL}/img/bicycle.svg`} alt="Data Brno logo" />
                        </div>
                    </CustomTooltip>
                    <CustomTooltip title={t("tooltips.info.sharedBicycle")}>
                        <div>
                            <img className="data-brno" src={`${PUBLIC_URL}/img/sharedBike.svg`} alt="Data Brno logo" />
                        </div>
                    </CustomTooltip>
                </div>
            </div>

            {/* Motivation */}
            <div className="about-section">
                <p className="about-header">{t("info.overview.whyApp")}</p>
                <p>
                    {t("info.overview.whyAppSection1")}<br/>
                    {t("info.overview.whyAppSection2")}<br/>
                    {t("info.overview.whyAppSection3")}
                </p>
            </div>

            {/* External services and data sources */}
            <div className="about-section">
                <p className="about-header">{t("info.overview.external")}</p>
                <div className="about-external">
                    <a href="https://data.brno.cz/" target="_blank" rel="noreferrer" className="external-item">
                        <img className="data-brno" src={`${PUBLIC_URL}/img/dataBrnoLogo.svg`} alt="Data Brno logo" />
                        <div className="external-text">
                            <h4>data.Brno</h4>
                            <p>{t("info.overview.externalSectionDB")}</p>
                        </div>
                    </a>

                    <a href="https://docs.opentripplanner.org/" target="_blank" rel="noreferrer" className="external-item">
                        <img src={`${PUBLIC_URL}/img/otpLogo.svg`} alt="OpenTripPlanner logo" />
                        <div className="external-text">
                            <h4>OpenTripPlanner</h4>
                            <p>{t("info.overview.externalSectionOTP")}</p>
                        </div>
                    </a>

                    <a href="https://dexter.fit.vutbr.cz/lissy/" target="_blank" rel="noreferrer" className="external-item">
                        <img src={`${PUBLIC_URL}/img/lissyLogo.svg`} alt="Lissy API logo" />
                        <div className="external-text">
                            <h4>Lissy</h4>
                            <p>{t("info.overview.externalSectionLissy")}</p>
                        </div>
                    </a>

                    <a href="https://nextbikeczech.com/" target="_blank" rel="noreferrer" className="external-item">
                        <img src={`${PUBLIC_URL}/img/nextbikeLogo.svg`} alt="Nextbike logo" />
                        <div className="external-text">
                            <h4>Nextbike</h4>
                            <p>{t("info.overview.externalSectionNextbike")}</p>
                        </div>
                    </a>

                    <a href="https://www.openstreetmap.org/" target="_blank" rel="noreferrer" className="external-item">
                        <img src={`${PUBLIC_URL}/img/osmLogo.svg`} alt="OpenStreetMap logo" />
                        <div className="external-text">
                            <h4>OpenStreetMap</h4>
                            <p>{t("info.overview.externalSectionOSM")}</p>
                        </div>
                    </a>
                </div>
            </div>

            <div className="about-section">
                <p className="about-header">{t("info.overview.contact")}</p>
                <p className="about-intro">
                    {t("info.overview.contactSection")}{" "} 
                    <a className="contact-mail" href="mailto:svitkovaandrea0@gmail.com">
                        svitkovaandrea0@gmail.com
                    </a>
                </p>
            </div>
        </div>
    );
}

export default About;

/** End of file About.tsx */
