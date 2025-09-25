/**
 * @file Logo.tsx
 * @brief Displays the logo in the planning sidebar
 * @author Andrea Svitkova (xsvitka00)
 */

import "./Logo.css";

function Logo() {
    return (
        <div className="logo">
            <img src="./logo.png" alt="Logo" />
            <img src="./logo-text.png" alt="Logo-text" />
        </div>
    );
}

export default Logo;

/** End of file Logo.tsx */
