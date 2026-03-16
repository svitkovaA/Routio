/**
 * @file Features.tsx
 * @brief Component for displaying other information about the application
 * @author Andrea Svitkova (xsvitka00)
 */

import TimelineIcon from '@mui/icons-material/Timeline';
import ExploreIcon from '@mui/icons-material/Explore';
import StraightenIcon from '@mui/icons-material/Straighten';
import "./Features.css"

function Features() {
    return(
        <div className="about-wrapper">
            <div className="about-section">
                <p className="about-header">Výpočet trasy</p>
                <div>
                    Aplikácia pri multimodálnom plánovaní vyberá najvhodnejšiu stanicu zdieľaných bicyklov. Výber stanice je založený na hodnotení viacerých faktorov, ktoré ovplyvňujú pravdepodobnosť úspešného prevzatia alebo vrátenia bicykla a komfort. Pri výbere stanice sú zohľadňované:
                    <ul className="features-list">
                        <li className="features-item">
                            <TimelineIcon className="features-icon" />

                            <div className="feature-content">
                                <strong className="feature-title">
                                    Predikcia dostupnosti zdieľaných bicyklov.
                                </strong>
                                <div>
                                    Predikovaný počet dostupných bicyklov v čase očakávaného príchodu do stanice
                                </div>
                            </div>
                        </li>

                        <li className="features-item">
                            <ExploreIcon className="features-icon" />

                            <div className="feature-content">
                                <strong className="feature-title">
                                    Uhol voči plánovanej trase.
                                </strong>
                                <div>
                                    Uhol medzi smerom plánovanej trasy a smerom k stanici, ktorý vyjadruje mieru odchýlky od pôvodnej trasy.
                                </div>
                            </div>
                        </li>

                        <li className="features-item">
                            <StraightenIcon className="features-icon" />

                            <div className="feature-content">
                                <strong className="feature-title">
                                    Vzdialenosť od bodu trasy
                                </strong>
                                <div>
                                    Vzdialenosť stanice od bodu trasy.
                                </div>
                            </div>
                        </li>
                    </ul>

                    Každému z týchto faktorov je priradená váha. Na základe ich kombinácie aplikácia vypočíta hodnotu pre jednotlivé stanice a vyberie tú, ktorá je pre danú trasu najvhodnejšia.
                </div>
            </div>

            <div className="about-section">
                <p className="about-header">Predikcia dostupnosti bicykla</p>
                <p>
                    Aplikácia využíva model hlbokého učenia na predikciu dostupnosti zdieľaných bicyklov v staniciach až na 24 hodín dopredu. Vďaka tomu môže aplikácia pri plánovaní trasy vybrať stanicu, pri ktorej je vyššia pravdepodobnosť, že v nej bude bicykel dostupný v čase príchodu.
                </p>
            </div>

            <div className="about-section">
                <p className="about-header">Zmena stanice zdieľaného bicykla a stojanu na vlastný bicykel</p>
                <p>
                    Nakoľko aplikácia vyberá jednu najlepšie ohodnotenú stanicu/bicykel. Preto má užívateľ možnosť túto stanicu/stojan zmeniť. Po zmene stanice/stojana aplikácia prepočíta zmenenú časť trasy a aktualizuje trasu.
                </p>
                {/* <div className="feature-video">
                    <video
                        src="/changeBikeStation.mp4"
                        autoPlay
                        loop
                        muted
                        playsInline
                        className="video"
                    />
                </div> */}

            </div>
        </div>
    );
}

export default Features;

/** End of file Features.tsx */
