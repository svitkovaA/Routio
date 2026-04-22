/**
 * @file HowToUse.tsx
 * @brief Component for displaying information about the application usage
 * @author Andrea Svitkova (xsvitka00)
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { PUBLIC_URL } from "../../config/config";
import KeyboardArrowLeftIcon from '@mui/icons-material/KeyboardArrowLeft';
import { Trans } from "react-i18next";
import "./HowToUse.css";

type SliderProps = {
    items: string[];                        // List of image URLS
    onChange?: (index: number) => void;     // Callback when slide changes
};

/**
 * Image slider with navigation
 */
function Slider({
    items,
    onChange
}: SliderProps) {
    // Current slide index
    const [current, setCurrent] = useState(0);

    // Update current slide
    const update = (newIndex: number) => {
        setCurrent(newIndex);
        onChange?.(newIndex);
    };

    // Move to next slide
    const nextSlide = () => {
        update((current + 1) % items.length);
    };

    // Move to previous slide
    const prevSlide = () => {
        update((current - 1 + items.length) % items.length);
    };

    return (
        <div className="how-to-img-slider">
            {/* Display current image */}
            <img src={items[current]} className="slider-media" />

            {/* Show navigation if multiple images exist */}
            {items.length > 1 && (
                <div className="arrows">
                    <button className="arrow left" onClick={prevSlide}>
                        <KeyboardArrowLeftIcon />
                    </button>

                    <div className="slider-cnt">
                        {current + 1}/{items.length}
                    </div>

                    {/* Slider counter */}
                    <button className="arrow right" onClick={nextSlide}>
                        <KeyboardArrowLeftIcon sx={{ transform: 'rotate(180deg)' }} />
                    </button>
                </div>
            )}
        </div>
    );
}

type HowToUseProps = {
    step: number;                       // Currently selected step
    setStep: (value: number) => void;   // Setter for step navigation
}

/**
 * Component rendering step by step instructions
 */
function HowToUse({
    step,
    setStep
} : HowToUseProps) {
    // Translation function
    const { t, i18n } = useTranslation();

    // Current slide within step
    const [currentSlide, setCurrentSlide] = useState(0);

    // Mapping of steps to image filenames
    const MEDIA_MAP = {
        step1: [
            "01a_input_form.png",
            "01b_input_form.png",
        ],
        step2: [
            "02_preferences.png"
        ],
        step3: [
            "03_results.png"
        ],
        step4: [
            "04a_detail.png",
            "04b_detail.png"
        ]
    } as const;

    // Construct image URL based on the used language
    const getImg = (lang: string, name: string) => `${PUBLIC_URL}img/${lang}/${name}`;

    // Resolve image paths for current step
    const items = MEDIA_MAP[`step${step}` as keyof typeof MEDIA_MAP]
        .map(src => getImg(i18n.language.split("-")[0], src));

    // Available instruction steps
    const steps = [
        { id: 1, title: t("info.howToUse.steps.planning") },
        { id: 2, title: t("info.howToUse.steps.preferences") },
        { id: 3, title: t("info.howToUse.steps.results") },
        { id: 4, title: t("info.howToUse.steps.detail") },
    ];

    return (
        <div className="about-section">
            {/* Section title */}
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
                    {steps.slice(2).map((s) => (
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
                {/* Step 1 content */}
                {step === 1 && (
                    <>
                        <div className="how-to-flex">
                            <Slider items={items} onChange={setCurrentSlide} />

                            <div className="how-to-right">
                                {currentSlide === 0 && (
                                    <>
                                        <div className="how-to-bold">
                                            {t("info.howToUse.step1.title")}
                                        </div>

                                        <div>
                                            <Trans i18nKey="info.howToUse.step1.desc" />
                                        </div>

                                        <div className="about-header small">
                                            {t("info.howToUse.step1.routePoints")}
                                        </div>

                                        <ul className="how-to-list">
                                            <li>{t("info.howToUse.step1.routePointsList.search")}</li>
                                            <li>{t("info.howToUse.step1.routePointsList.map")}</li>
                                            <li>{t("info.howToUse.step1.routePointsList.coords")}</li>
                                            <li>{t("info.howToUse.step1.routePointsList.context")}</li>
                                            <li>{t("info.howToUse.step1.routePointsList.current")}</li>
                                            <li>{t("info.howToUse.step1.routePointsList.bikeStations")}</li>
                                        </ul>
                                    </>
                                )}

                                {currentSlide === 1 && (
                                    <>
                                        <div className="how-to-bold">
                                            {t("info.howToUse.step1Bike.title")}
                                        </div>

                                        <div>
                                            <Trans i18nKey="info.howToUse.step1Bike.desc" />
                                        </div>

                                        <div className="about-header small">
                                            {t("info.howToUse.step1Bike.add")}
                                        </div>

                                        <ul className="how-to-list">
                                            <li>{t("info.howToUse.step1Bike.list.click")}</li>
                                            <li>{t("info.howToUse.step1Bike.list.type")}</li>
                                            <li>{t("info.howToUse.step1Bike.list.position")}</li>
                                            <li>{t("info.howToUse.step1Bike.list.insert")}</li>
                                        </ul>
                                    </>
                                )}
                            </div>
                        </div>
                    </>
                )}

                {/* Step 2 content */}
                {step === 2 && (
                    <>
                        <div className="how-to-flex">
                            <Slider items={items} />
                            <div className="how-to-right">
                                <div className="how-to-bold">
                                   {t("info.howToUse.step2.title")}
                                </div>
                                <div>
                                    <div className="about-header small">
                                       {t("info.howToUse.step2.title")}
                                    </div>
                                    <ul className="how-to-list">
                                        <li><Trans i18nKey="info.howToUse.step2.transportList.transfers" /></li>
                                        <li><Trans i18nKey="info.howToUse.step2.transportList.modes" /></li>
                                        <li><Trans i18nKey="info.howToUse.step2.transportList.delays" /></li>
                                    </ul>
                                </div>
                                <div>
                                    <div className="about-header small">
                                        {t("info.howToUse.step2.bike")}
                                    </div>
                                    <ul className="how-to-list">
                                        <li><Trans i18nKey="info.howToUse.step2.bikeList.distance" /></li>
                                        <li><Trans i18nKey="info.howToUse.step2.bikeList.speed" /></li>
                                        <li><Trans i18nKey="info.howToUse.step2.bikeList.lock" /></li>
                                    </ul>
                                </div>
                                <div>
                                    <div className="about-header small">
                                        {t("info.howToUse.step2.walk")}
                                    </div>
                                    <ul className="how-to-list">
                                        <li><Trans i18nKey="info.howToUse.step2.walkList.distance" /></li>
                                        <li><Trans i18nKey="info.howToUse.step2.walkList.speed" /></li>
                                    </ul>
                                </div>
                            </div>

                        </div>
                    </>
                )}

                {/* Step 3 content */}
                {step === 3 && (
                    <>
                        <div className="how-to-flex">
                            <Slider items={items} />
                            <div className="how-to-right">
                                <div className="how-to-bold">
                                    {t("info.howToUse.step3.title")}
                                </div>
                                <div>
                                    <div className="about-header small">
                                       {t("info.howToUse.step3.overview")}
                                    </div>
                                    <ul className="how-to-list">
                                        <li><Trans i18nKey="info.howToUse.step3.overviewList.map" /></li>
                                        <li><Trans i18nKey="info.howToUse.step3.overviewList.time" /></li>
                                        <li><Trans i18nKey="info.howToUse.step3.overviewList.details" /></li>
                                    </ul>
                                </div>
                                <div>
                                    <div className="about-header small">
                                        {t("info.howToUse.step3.visual")}
                                    </div>
                                    <ul className="how-to-list">
                                        <li><Trans i18nKey="info.howToUse.step3.visualList.colors" /></li>
                                    </ul>
                                </div>
                                <div>
                                    <div className="about-header small">
                                        {t("info.howToUse.step3.detail")}
                                    </div>
                                    <ul className="how-to-list">
                                        <li><Trans i18nKey="info.howToUse.step3.detailList.click" /></li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </>
                )}

                {/* Step 4 content */}
                {step === 4 && (
                    <>
                        <div className="how-to-flex">
                            <Slider
                                items={items}
                                onChange={setCurrentSlide}
                            />
                            <div className="how-to-right">
                                {currentSlide === 0 && (
                                    <>
                                        <div className="how-to-bold">
                                           {t("info.howToUse.step4.public.title")}
                                        </div>

                                        <div>
                                            <div className="about-header small">
                                               {t("info.howToUse.step4.public.info")}
                                            </div>
                                            <ul className="how-to-list">
                                                <li><Trans i18nKey="info.howToUse.step4.public.infoList.line" /></li>
                                                <li><Trans i18nKey="info.howToUse.step4.public.infoList.zones" /></li>
                                                <li><Trans i18nKey="info.howToUse.step4.public.infoList.length" /></li>
                                            </ul>
                                        </div>

                                        <div>
                                            <div className="about-header small">
                                                {t("info.howToUse.step4.public.departures")}
                                            </div>
                                            <ul className="how-to-list">
                                                <li><Trans i18nKey="info.howToUse.step4.public.departuresList.next" /></li>
                                                <li><Trans i18nKey="info.howToUse.step4.public.departuresList.select" /></li>
                                                <li><Trans i18nKey="info.howToUse.step4.public.departuresList.stops" /></li>
                                            </ul>
                                        </div>

                                        <div>
                                            <div className="about-header small">
                                                {t("info.howToUse.step4.public.delays")}
                                            </div>
                                            <ul className="how-to-list">
                                                <li><Trans i18nKey="info.howToUse.step4.public.delaysList.current" /></li>
                                                <li><Trans i18nKey="info.howToUse.step4.public.delaysList.history" /></li>
                                                <li><Trans i18nKey="info.howToUse.step4.public.delaysList.position" /></li>
                                            </ul>
                                        </div>
                                    </>
                                )}
                                {currentSlide === 1 && (
                                    <>
                                        <div className="how-to-bold">
                                            {t("info.howToUse.step4.bikeWalk.title")}
                                        </div>

                                        <div>
                                            <div className="about-header small">
                                                {t("info.howToUse.step4.bikeWalk.bike")}
                                            </div>
                                            <ul className="how-to-list">
                                                <li><Trans i18nKey="info.howToUse.step4.bikeWalk.bikeList.lock" /></li>
                                                <li><Trans i18nKey="info.howToUse.step4.bikeWalk.bikeList.length" /></li>
                                                <li><Trans i18nKey="info.howToUse.step4.bikeWalk.bikeList.elevation" /></li>
                                            </ul>
                                        </div>

                                        <div>
                                            <div className="about-header small">
                                                {t("info.howToUse.step4.bikeWalk.sharedBike")}
                                            </div>
                                            <ul className="how-to-list">
                                                <li><Trans i18nKey="info.howToUse.step4.bikeWalk.sharedBikeList.current" /></li>
                                                <li><Trans i18nKey="info.howToUse.step4.bikeWalk.sharedBikeList.expected" /></li>
                                            </ul>
                                        </div>

                                        <div>
                                            <div className="about-header small">
                                                {t("info.howToUse.step4.bikeWalk.walk")}
                                            </div>
                                            <ul className="how-to-list">
                                                <li><Trans i18nKey="info.howToUse.step4.bikeWalk.walkList.length" /></li>
                                                <li><Trans i18nKey="info.howToUse.step4.bikeWalk.walkList.elevation" /></li>
                                            </ul>
                                        </div>
                                    </>
                                )}
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}

export default HowToUse;

/** End of file HowToUse.tsx */
