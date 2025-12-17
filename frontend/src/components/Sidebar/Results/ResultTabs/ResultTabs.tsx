/**
 * @file ResultTabs.tsx
 * @brief Displays mode selection tabs for viewing different trip results
 * @author Andrea Svitkova (xsvitka00)
 */

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faBusSimple, faBicycle, faPersonWalking } from "@fortawesome/free-solid-svg-icons";
import { MultimodalIcon } from "../../Planning/Icons/Icons";
import "./ResultTabs.css";
import { useInput } from "../../../InputContext";
import { useResult } from "../../../ResultContext";

function ResultTabs() {  
    const {
        setSelectedTripPatternIndex,
        resultActiveIndex ,setResultActiveIndex
    } = useResult();

    const { setMode } = useInput();

    return (
        <div className="result-tabs" onClick={() => setSelectedTripPatternIndex(0)}>
            <div 
                className={"result-mode " + (resultActiveIndex === 0 ? "selected" : "")}
                onClick={() => {
                    setResultActiveIndex(0);
                    setMode("transit,bicycle,walk"); 
                }}
            >
                <MultimodalIcon />
            </div>
            <div 
                className={"result-mode " + (resultActiveIndex === 1 ? "selected" : "")} 
                onClick={() => {
                    setResultActiveIndex(1);
                    setMode("walk_transit");
                }}
            >
                <div className="circle">
                    <FontAwesomeIcon icon={faBusSimple} />
                </div>
            </div>
            <div 
                className={"result-mode " + (resultActiveIndex === 2 ? "selected" : "")}
                onClick={() => {
                    setResultActiveIndex(2);
                    setMode("bicycle");
                }}
            >
                <div className="circle">
                    <FontAwesomeIcon icon={faBicycle} />
                </div>
            </div>
            <div 
                className={"result-mode " + (resultActiveIndex === 3 ? "selected" : "")}
                onClick={() => {
                    setResultActiveIndex(3);
                    setMode("foot");
                }}
            >
                <div className="circle">
                    <FontAwesomeIcon icon={faPersonWalking} />
                </div>
            </div>
        </div>
    );
}

export default ResultTabs;

/** End of file ResultTabs.tsx */
