/**
 * @file Logo.tsx
 * @brief Displays the logo in the planning sidebar
 * @author Andrea Svitkova (xsvitka00)
 */

import "./Logo.css";
import { PUBLIC_URL } from "../../../config/config";

function Logo() {

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
