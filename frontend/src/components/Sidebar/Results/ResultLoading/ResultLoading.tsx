/**
 * @file ResultLoading.tsx
 * @brief Displays a loading screen while trip data are being fetched
 * @author Andrea Svitkova (xsvitka00)
 */

import "./ResultLoading.css";

function ResultLoading() {
    return (
        <div className="result-loading-wrapper">
            <div className="result-loading-timeline"></div>
            <div className="result-loading-grid">
                <div className="result-loading-info"></div>
                <div className="result-loading-info"></div>
                <div className="result-loading-info"></div>
            </div>
        </div>
    );
}

export default ResultLoading;

/** End of file ResultLoading.tsx */
