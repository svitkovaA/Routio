/**
 * @file Suggestions.tsx
 * @brief Displays component rendering a list of location suggestions for input fields
 * @author Andrea Svitkova (xsvitka00)
 */

import { InputText } from "../../../../types/types";
import './Suggestions.css'

type SuggestionsProps = {
    suggestions: InputText[];
    handleSuggestionClick: (suggestion: InputText) => void;
    highlightedIndex: number;
    render: boolean;
    style?: React.CSSProperties;
}

function Suggestions ({
    suggestions,
    handleSuggestionClick,
    highlightedIndex,
    render,
    style
} : SuggestionsProps) {
    if (!render) {
        return null;
    }

    return (
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
