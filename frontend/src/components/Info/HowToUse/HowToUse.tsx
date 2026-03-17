/**
 * @file HowToUse.tsx
 * @brief Component for displaying information about the application usage
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { PUBLIC_URL } from "../../config/config";
import KeyboardArrowLeftIcon from '@mui/icons-material/KeyboardArrowLeft';
import "./HowToUse.css";

function HowToUse() {
    // Translation function
    const { t } = useTranslation();
    
    // Currently selected instruction step
    const [step, setStep] = useState(1);

    const [current, setCurrent] = useState(0);

    const images = [
        `${process.env.PUBLIC_URL}/img/04_detail_b.png`,
        `${process.env.PUBLIC_URL}/img/04_detail_bike.png`,
    ];

    const nextSlide = () => {
        setCurrent((prev) => (prev + 1) % images.length);
    };

    const prevSlide = () => {
        setCurrent((prev) => (prev - 1 + images.length) % images.length);
    };

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
                        {/* <img src={`${PUBLIC_URL}/img/01_input_f.png`} alt="Plánovanie" /> */}
                        <p>
                            {/* {t("info.howToUse.steps.planningSection")} */}
                            Zadajte východiskový a cieľový bod, prípadne medzibody, nastavte dátum a čas a upravte preferencie plánovania trasy.
                        </p>
                        <div className="about-header">
                            Body trasy je možné vybrať jedným z následujúcich spôsobov:
                        </div>
                        <ul className="how-to-points">
                            <li>
                                Zadaním <strong>názvu lokality</strong> do vstupného poľa.
                            </li>

                            <li>
                                Výberom polohy <strong>priamo z mapy</strong>, a to kliknutím na ikonu bodu a následným výberom miesta na mape.
                            </li>

                            <li>
                                <strong>Zadaním geografických súradníc</strong> do vstupného poľa.
                            </li>

                            <li>
                                Výber bodu <strong>z kontextového menu mapy</strong>, a to prostredníctvom pravého kliknutia na mapový podklad a následným
                                výberom o ktorý bod sa jedná.
                            </li>
                        </ul>
                    </>
                )}

                {step === 2 && (
                    <>
                        {/* <img src={`${PUBLIC_URL}/img/02_pref.png`} alt="Preferencie" /> */}
                        <p>
                            Nastavte preferencie plánovania, ako sú zohľadňované druhy dopravy alebo obmedzenia.
                        </p>
                    </>
                )}

                {step === 3 && (
                    <>
                        {/* <img src={`${PUBLIC_URL}/img/03_res.png`} alt="Výsledky" /> */}
                        <p>
                            Výsledky plánovania sú zobrazené na mape ako aj v textovej podobe.
                        </p>
                    </>
                )}

                {step === 4 && (
                    <div className="how-to-img-slider">

                        {/* <img src={images[current]} alt="Detail" className="slider-image" /> */}
                        <div className="arrows">
                            <button className="arrow left" onClick={prevSlide}>
                                <KeyboardArrowLeftIcon />
                            </button>
                            <div className="slider-cnt">
                                {current + 1}/{images.length}
                            </div>
                            <button className="arrow right" onClick={nextSlide}>
                                <KeyboardArrowLeftIcon sx={{ transform: 'rotate(180deg)' }} />
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default HowToUse;

/** End of file HowToUse.tsx */
