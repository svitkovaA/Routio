import "./About.css"

function About() {
    return(
        <div className="about">
            <h4>O aplikácii</h4>
            <p className="about-intro">
                Táto aplikácia poskytuje podporu pre plánovanie ciest s využitím verejnej dopravy, bicykla vrátane systému zdieľaných bicyklov a chôdze. Okrem základnej unimodálnej dopravy ponúka podporu pre multimodálne plánovanie ciest s využitím kombinácie vyššie uvedených druhov dopravy.
            </p>

            <h4>Čo aplikácia ponúka?</h4>
            <ul className="about-features">
                <li>Kombinovanie verejnej dopravy, bicykla a chôdze</li>
                <li>Prehľadné zobrazenie trasy na mape</li>
                <li>Porovnanie alternatívnych trás</li>
                <li>Možnosť prispôsobiť si preferencie plánovania</li>
            </ul>
        </div>
    );
}

export default About;
