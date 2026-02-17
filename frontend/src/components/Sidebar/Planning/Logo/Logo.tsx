/**
 * @file Logo.tsx
 * @brief Displays the logo
 * @author Andrea Svitkova (xsvitka00)
 */

import { PUBLIC_URL } from "../../../config/config";
import "./Logo.css";

function Logo() {
    /**
     * Reload when clicking on application logo
     */
    const handleClick = () => {
        window.location.reload();
    };
    return (
        <div className="logo">
            <img src={`${PUBLIC_URL}/routioLogo.png`} alt="Logo" onClick={handleClick} />
            <img src={`${PUBLIC_URL}/routioText.png`} alt="Logo-text" onClick={handleClick}/>
        </div>
    );
}

export default Logo;

/** End of file Logo.tsx */
