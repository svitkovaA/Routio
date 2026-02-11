/**
 * @file Logo.tsx
 * @brief Displays the logo in the planning sidebar
 * @author Andrea Svitkova (xsvitka00)
 */

import "./Logo.css";
import { PUBLIC_URL } from "../../../config/config";

function Logo() {
    return (
        <div className="logo">
            <img src={`${PUBLIC_URL}/logo.png`} alt="Logo" />
            <img src={`${PUBLIC_URL}/logo-text.png`} alt="Logo-text" />
        </div>
    );
}

export default Logo;

/** End of file Logo.tsx */
