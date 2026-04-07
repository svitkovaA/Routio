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

type MediaItem = {
    type: "image" | "video";
    src: string;
};

function MediaSlider({ items }: { items: MediaItem[] }) {
    const [current, setCurrent] = useState(0);

    const nextSlide = () => {
        setCurrent((prev) => (prev + 1) % items.length);
    };

    const prevSlide = () => {
        setCurrent((prev) => (prev - 1 + items.length) % items.length);
    };

    return (
        <div className="how-to-img-slider">
            {items[current].type === "image" ? (
                <img src={items[current].src} className="slider-media" />
            ) : (
                <video
                    src={items[current].src}
                    className="slider-media video"
                    autoPlay
                    muted
                    loop
                />
            )}

            {items.length > 1 && (
                <div className="arrows">
                    <button className="arrow left" onClick={prevSlide}>
                        <KeyboardArrowLeftIcon />
                    </button>

                    <div className="slider-cnt">
                        {current + 1}/{items.length}
                    </div>

                    <button className="arrow right" onClick={nextSlide}>
                        <KeyboardArrowLeftIcon sx={{ transform: 'rotate(180deg)' }} />
                    </button>
                </div>
            )}
        </div>
    );
}

type HowToUseProps = {
    step: number;
    setStep: (value: number) => void;
}

function HowToUse({
    step,
    setStep
} : HowToUseProps) {
    // Translation function
    const { t, i18n } = useTranslation();

    const MEDIA_MAP = {
        step1: [
            { type: "image", src: "01a_input_form.png" },
            { type: "video", src: "demo1.mp4" },
        ],
        step2: [
            { type: "image", src: "02_pref.png" }
        ],
        step3: [
            { type: "image", src: "03_res.png" }
        ],
        step4: [
            { type: "image", src: "04_detail_b.png" },
            { type: "image", src: "04_detail_bike.png" }
        ]
    } as const;

    const getLang = (lang: string) => lang.split("-")[0];

    const getImg = (lang: string, name: string) =>
        `${PUBLIC_URL}img/${lang}/${name}`;

    const lang = getLang(i18n.language);

    const items = MEDIA_MAP[`step${step}` as keyof typeof MEDIA_MAP]
        .map(item => ({
            ...item,
            src: getImg(lang, item.src)
        }));


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
                {step === 1 && (
                    <>
                        <MediaSlider items={items} />
                        <p>
                            Zadajte východiskový a cieľový bod, prípadne medzibody, nastavte dátum a čas a upravte preferencie plánovania trasy.
                        </p>
                        <div className="about-header">
                            Výber bodov trasy
                        </div>
                        Body trasy je možné vybrať jedným z následujúcich spôsobov
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

                            <li>
                                Na základe aktuálnej polohy.
                            </li>
                        </ul>

                        <div className="about-header">
                            Výber stanice zdieľaných bicyklov (obrázok 2)
                        </div>
                        <div>
                            Stanice zdieľaných bicyklov je možné nastaviť vybraním zdieľaného bicykla a následným povolením zobrazenia.<br/>

                            Pridanie stanice zdieľaného bicykla ako bodu trasy:
                            Stanicu je možné použiť ako bod trasy, a to kliknutím na príslušnú stanicu, nastavením,či ide o počiatočnú alebo cieľovú stanicu a vybraním bodu, na ktorý sa stanica premietne. V prípade pridania ako nového bodu je stanica automaticky pridaná pred koniec trasy a je potrebné ju umiestniť na požadované miesto.
                        </div>
                    </>
                )}

                {step === 2 && (
                    <>
                        <MediaSlider items={items} />
                        <p>
                            Nastavte preferencie plánovania, ako sú zohľadňované druhy dopravy alebo obmedzenia.
                        </p>
                    </>
                )}

                {step === 3 && (
                    <>
                        <MediaSlider items={items} />
                        <p>
                            Výsledky plánovania sú zobrazené na mape ako aj v textovej podobe.
                        </p>
                    </>
                )}

                {step === 4 && (
                    <MediaSlider items={items} />
                )}
            </div>
        </div>
    );
}

export default HowToUse;

/** End of file HowToUse.tsx */
