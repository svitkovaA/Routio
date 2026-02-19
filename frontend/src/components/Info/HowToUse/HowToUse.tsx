/**
 * @file HowToUse.tsx
 * @brief Component for displaying information about the application usage
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { PUBLIC_URL } from "../../config/config";
import "./HowToUse.css";

function HowToUse() {
    // Translation function
    const { t } = useTranslation();
    
    // Currently selected instruction step
    const [step, setStep] = useState(1);

    // Available instruction steps
    const steps = [
        { id: 1, title: t("info.howToUse.steps.planning") },
        { id: 2, title: t("info.howToUse.steps.preferences") },
        { id: 3, title: t("info.howToUse.steps.results") },
        { id: 4, title: t("info.howToUse.steps.detail") },
    ];

    return (
        <div className="about-section">
            <div className="about-header">
                {t("info.howToUse.howToPlan")}
            </div>

            {/* Step navigation */}
            <div className="howto-steps">
                <div className="howto-steps-tuple">
                    {/* Fist two steps */}
                    {steps.slice(0,2).map((s, i) => (
                        <div
                            key={s.id}
                            className={"howto-step " + (step === s.id ? "active" : "")}
                            onClick={() => setStep(s.id)}
                        >
                            {i > 0 && <div className="howto-step-line" />}
                            <div className="step-circle">{s.id}</div>
                            <span>{s.title}</span>
                        </div>
                    ))}
                </div>
                <div className="howto-steps-tuple">
                    {/* Second two steps */}
                    {steps.slice(2).map((s, i) => (
                        <div
                            key={s.id}
                            className={"howto-step " + (step === s.id ? "active" : "")}
                            onClick={() => setStep(s.id)}
                        >
                            <div className="howto-step-line" />
                            <div className="step-circle">{s.id}</div>
                            <span>{s.title}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Step content */}
            <div className="howto-content">
                {step === 1 && (
                    <>
                        <p>
                            {t("info.howToUse.steps.planningSection")}
                        </p>
                        {/* <img src={`${PUBLIC_URL}/img/skuska.png`} alt="Plánovanie" /> */}
                    </>
                )}

                {step === 2 && (
                    <>
                        <p>
                            {t("info.howToUse.steps.preferencesSection")}
                        </p>
                        {/* <img src={`${PUBLIC_URL}/img/skuska.png`} alt="Preferencie" /> */}
                    </>
                )}

                {step === 3 && (
                    <>
                        <p>
                            {t("info.howToUse.steps.resultsSection")}
                        </p>
                        {/* <img src={`${PUBLIC_URL}/img/skuska.png`} alt="Výsledky" /> */}
                    </>
                )}

                {step === 4 && (
                    <>
                        <p>
                            {t("info.howToUse.steps.detailSection")}
                        </p>
                        {/* <img src={`${PUBLIC_URL}/img/skuska.png`} alt="Detail" /> */}
                    </>
                )}
            </div>
        </div>
    );
}

export default HowToUse;

/** End of file HowToUse.tsx */
