/**
 * @file HowToUse.tsx
 * @brief Component for displaying information about the application usage
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from "react";
import { PUBLIC_URL } from "../../config/config";
import "./HowToUse.css";

function HowToUse() {
    // Currently selected instruction step
    const [step, setStep] = useState(1);

    // Available instruction steps
    const steps = [
        { id: 1, title: "Plánovanie" },
        { id: 2, title: "Preferencie" },
        { id: 3, title: "Výsledky" },
        { id: 4, title: "Detail" },
    ];

    return (
        <div className="about-section">
            <div className="about-header">
                Ako naplánovať trasu
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
                            Vyplňte vstupný formulár zadaním dátumu a výberom bodov
                        </p>
                        {/* <img src={`${PUBLIC_URL}/img/skuska.png`} alt="Plánovanie" /> */}
                    </>
                )}

                {step === 2 && (
                    <>
                        <p>
                            Nastavte preferencie plánovania, ako sú preferované
                            druhy dopravy alebo obmedzenia
                        </p>
                        {/* <img src={`${PUBLIC_URL}/img/skuska.png`} alt="Preferencie" /> */}
                    </>
                )}

                {step === 3 && (
                    <>
                        <p>
                            Zobrazia sa dostupné spojenia vrátane
                            času, prestupov a jednotlivých úsekov trasy
                        </p>
                        {/* <img src={`${PUBLIC_URL}/img/skuska.png`} alt="Výsledky" /> */}
                    </>
                )}

                {step === 4 && (
                    <>
                        <p>
                            Detail trasy poskytuje presné informácie o jednotlivých
                            úsekoch a zastávkach
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
