import { useState } from "react";
import "./HowToUse.css";

const steps = [
    {
        title: "Parametre vyhľadávania",
        text: "Po spustení aplikácie sa zobrazí hlavné menu, kde si môžete zvoliť modul, s ktorým chcete pracovať.",
        // video: "/videos/uvod.mp4",
        description: (
            <div>
                <h4>Zadanie bodov trasy:</h4>
                <ul>
                    <li>Zadaním názvu budovy alebo ulice požadovanej lokality do textového vstupného poľa</li>
                    <li>Zadaním súradníc požadovanej lokality do textového vstupného poľa</li>
                    <li>Kliknutím na ikonu polohy v textovom vstupnom poli a následnom výbere bodu z mapy</li>
                    <li>Pravým kliknutím na lokalitu na mape a výber o ktorý bod ide</li>
                </ul>

                <h4>Nastavenie dátumu a času vyhľadávania trasy:</h4>
                <p>Dátum a čas je možné zadať zadaním hodnoty v príslušnom tvare do vstupného poľa alebo kliknutím na ikonu vo vstupnom poli a výberom hodnoty.</p>

                <h4>Nastavenie možností trasy:</h4>
            </div>
        )

    },
    {
        title: "Pokročilé možnosti vyhľadávania",
        text: "Zadajte počiatočný a cieľový bod pomocou vyhľadávacieho poľa alebo priamo na mape.",
        // video: "/videos/howto-inputs.mp4",
        description: "ff"
    },
    {
        title: "Nájdené trasy",
        text: "Aplikácia ponúkne viacero možných trás, z ktorých si môžete vybrať.",
        // video: "/videos/howto-route.mp4",
        description: "ff"
    },
    {
        title: "Detail vyhľadávania",
        text: "Zobrazte si detaily trasy a upravte preferencie plánovania.",
        // video: "/videos/howto-details.mp4",
        description: "ff"
    }
];

function HowToUse() {
    const [activeStep, setActiveStep] = useState(0);

    return (
        <div className="howto">
            <div className="howto-steps">
                {steps.map((step, index) => (
                    <div
                        key={index}
                        className={`howto-step ${index === activeStep ? "active" : ""}`}
                        onClick={() => setActiveStep(index)}
                    >
                        <span className="step-number">{index + 1}</span>
                        <span className="step-title">{step.title}</span>
                    </div>
                ))}
            </div>

            <div className="howto-content">
                <h4>{steps[activeStep].title}</h4>
                <p>{steps[activeStep].text}</p>

                <video
                    // key={steps[activeStep].video}
                    className="howto-video"
                    autoPlay
                    muted
                    loop
                    playsInline
                >
                    {/* <source src={steps[activeStep].video} type="video/mp4" /> */}
                </video>

                <div className="step-title">{steps[activeStep].description}</div>

            </div>
        </div>
    );
}

export default HowToUse;
