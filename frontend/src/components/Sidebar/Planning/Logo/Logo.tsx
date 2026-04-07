/**
 * @file Logo.tsx
 * @brief Displays the logo
 * @author Andrea Svitkova (xsvitka00)
 */

import { PUBLIC_URL } from "../../../config/config";
import "./Logo.css";

function Logo() {
    return (
        <div className="logo">
            <img src={`${PUBLIC_URL}routioLogo.png`} alt="Logo"/>
            <img src={`${PUBLIC_URL}routioText.png`} alt="Logo-text" />
        </div>
    );
}

export default Logo;

/** End of file Logo.tsx */
