/**
 * @file Contact.tsx
 * @brief Component for displaying contact information
 * @author Andrea Svitkova (xsvitka00)
 */

import "./Contact.css"

function Contact() {
    return (
        <div className="about-wrapper">
            <div className="about-section">
                <p className="about-header">Kontakt</p>

                <p className="about-intro">
                    V prípade otázok, pripomienok alebo návrhov na zlepšenie aplikácie
                    ma môžete kontaktovať prostredníctvom e-mailu:{" "} 
                    <a className="contact-mail" href="mailto:svitkovaandrea0@gmail.com">
                        svitkovaandrea0@gmail.com
                    </a>
                </p>
            </div>
        </div>
    );
}

export default Contact;

/** End of file Contact.tsx */
