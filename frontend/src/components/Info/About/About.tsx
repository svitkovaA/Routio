/**
 * @file About.tsx
 * @brief Component for displaying general information abut the application
 * @author Andrea Svitkova (xsvitka00)
 */

import { PUBLIC_URL } from "../../config/config";
import "./About.css";

function About() {
    return (
        <div className="about-wrapper">

            {/* Application overview */}
            <div className="about-section">
                <p className="about-header">O aplikácii</p>
                <p>
                    Táto práca vznikla ako súčasť bakalárskej práce na FIT VUT 
                    pod vedením Ing. Jiřího Hynka, PhD. Aplikácia poskytuje podporu pre plánovanie unimodálnych ciest,
                    kde je využitý jeden druh dopravy, ako aj multimodálnych trás
                    s kombináciou viacerých druhov dopravy v rámci jednej trasy.
                </p>
            </div>

            {/* Supported transport modes */}
            <div className="about-section">
                <p className="about-header">Podporované druhy dopravy</p>
                <div className="about-transport-modes">
                    <div>
                        <img className="data-brno" src={`${PUBLIC_URL}/img/publicTransport.svg`} alt="Data Brno logo" />
                    </div>
                    <div>
                        <img className="data-brno" src={`${PUBLIC_URL}/img/foot.svg`} alt="Data Brno logo" />
                    </div>
                    <div>
                        <img className="data-brno" src={`${PUBLIC_URL}/img/bicycle.svg`} alt="Data Brno logo" />
                    </div>
                    <div>
                        <img className="data-brno" src={`${PUBLIC_URL}/img/sharedBike.svg`} alt="Data Brno logo" />
                    </div>
                </div>
            </div>

            {/* Motivation */}
            <div className="about-section">
                <p className="about-header">Prečo aplikácia vznikla</p>
                <p>
                    Každodenná mobilita je neoddeliteľnou súčasťou života. 
                    Preprava môže prebiehať pomocou osobnej automobilovej dopravy, 
                    verejnej dopravy, chôdze alebo alternatívnych foriem, ako sú zdieľané bicykle.<br/>
                    
                    S rastúcimi mestami a zvyšujúcimi sa nárokmi na mobilitu však 
                    vzniká potreba efektívne kombinovať rôzne druhy dopravy. 
                    Existujúce riešenia často neposkytujú dostatočnú podporu 
                    pre integráciu zdieľanej cyklistiky do multimodálneho plánovania trás.<br/>

                    Cieľom tejto aplikácie bolo preto vytvoriť jednotnú aplikáciu, ktorá umožní kombinovať viacero druhov dopravy v rámci jednej trasy a poskytuje užívateľovi centralizované multimodálne plánovanie. 
                </p>
            </div>

            {/* External services and data sources */}
            <div className="about-section">
                <p className="about-header">Externé služby a dátové zdroje</p>
                <div className="about-external">
                    <a href="https://data.brno.cz/" target="_blank" rel="noreferrer" className="external-item">
                        <img className="data-brno" src={`${PUBLIC_URL}/img/dataBrnoLogo.svg`} alt="Data Brno logo" />
                        <div className="external-text">
                            <h4>data.Brno</h4>
                            <p>Otvorené dáta verejnej dopravy Juhomoravského kraja vo formáte GTFS a GTFS-RT</p>
                        </div>
                    </a>

                    <a href="https://docs.opentripplanner.org/" target="_blank" rel="noreferrer" className="external-item">
                        <img src={`${PUBLIC_URL}/img/otpLogo.svg`} alt="OpenTripPlanner logo" />
                        <div className="external-text">
                            <h4>OpenTripPlanner</h4>
                            <p>Nástroj pre plánovanie trás s využitím verejnej dopravy, chôdze a cyklistiky</p>
                        </div>
                    </a>

                    <a href="https://dexter.fit.vutbr.cz/lissy/" target="_blank" rel="noreferrer" className="external-item">
                        <img src={`${PUBLIC_URL}/img/lissyLogo.svg`} alt="Lissy API logo" />
                        <div className="external-text">
                            <h4>Lissy</h4>
                            <p>API poskytujúce informácie o tvary trás liniek a meškaniach spojov</p>
                        </div>
                    </a>

                    <a href="https://nextbikeczech.com/" target="_blank" rel="noreferrer" className="external-item">
                        <img src={`${PUBLIC_URL}/img/nextbikeLogo.svg`} alt="Nextbike logo" />
                        <div className="external-text">
                            <h4>Nextbike</h4>
                            <p>Informácie o zdieľaných bicykloch v staniciach v reálnom čase spoločnosti Nextbike</p>
                        </div>
                    </a>

                    <a href="https://www.openstreetmap.org/" target="_blank" rel="noreferrer" className="external-item">
                        <img src={`${PUBLIC_URL}/img/osmLogo.svg`} alt="OpenStreetMap logo" />
                        <div className="external-text">
                            <h4>OpenStreetMap</h4>
                            <p>Otvorené mapové podklady a informácie o dopravnej infraštruktúre</p>
                        </div>
                    </a>
                </div>
            </div>
        </div>
    );
}

export default About;

/** End of file About.tsx */
