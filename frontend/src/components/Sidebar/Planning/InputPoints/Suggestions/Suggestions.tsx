/**
 * @file Suggestions.tsx
 * @brief Component rendering a list of location suggestions for input fields
 * @author Andrea Svitkova (xsvitka00)
 */

import { PUBLIC_URL } from "../../../../config/config";
import type { Suggestion } from "../../../../types/types";
import './Suggestions.css'

type SuggestionsProps = {
    suggestions: Suggestion[];                              // Array of suggestions
    handleSuggestionClick: (suggestion: Suggestion) => void;// Handler triggered when suggestion is selected
    highlightedIndex: number;                               // Handler triggered when suggestion is selected
    render: boolean;                                        // Controls conditional rendering of suggestion list
    style?: React.CSSProperties;                            // Optional styles
}

function Suggestions ({
    suggestions,
    handleSuggestionClick,
    highlightedIndex,
    render,
    style
} : SuggestionsProps) {
    // Do not render suggestion list if render flag is false
    if (!render) {
        return null;
    }

    return (
        // Suggestion list container
        <ul className="suggestions-list" tabIndex={-1} style={style}>
            {suggestions.map((s, i) => (
                <li
                    key={i}
                    onMouseDown={() => handleSuggestionClick(s)}
                    className={`suggestion-item ${i === highlightedIndex ? "selected" : ""}`}
                >
                    {s.name}
                    {s.isBus && s.isTrain ? (
                        <img src={`${PUBLIC_URL}img/bus_train_stop.svg`} alt="Bus and train stop" />
                    ) : s.isBus ? (
                        <img src={`${PUBLIC_URL}img/bus_stop.svg`} alt="Bus stop" />
                    ) : s.isTrain ? (
                        <img src={`${PUBLIC_URL}img/train_stop.svg`} alt="Train stop" />
                    ) : null}
                </li>
            ))}
        </ul>
    );
}

export default Suggestions;

/* End of file Suggestions.tsx */
