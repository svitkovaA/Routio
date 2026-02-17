/**
 * @file Suggestions.tsx
 * @brief Component rendering a list of location suggestions for input fields
 * @author Andrea Svitkova (xsvitka00)
 */

import { InputText } from "../../../../types/types";
import './Suggestions.css'

type SuggestionsProps = {
    suggestions: InputText[];                               // Array of suggestions
    handleSuggestionClick: (suggestion: InputText) => void; // Handler triggered when suggestion is selected
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
                    {[s.name, s.street, s.city].filter(Boolean).join(", ")}
                </li>
            ))}
        </ul>
    );
}

export default Suggestions;

/* End of file Suggestions.tsx */
