/**
 * @file Icons.tsx
 * @brief Provides icons for transport modes, multimodal trips, accuracy indicators, and timeline display
 * @author Andrea Svitkova (xsvitka00)
 */

import { JSX } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faBusSimple, faBicycle, faPersonWalking, faCrosshairs, faCircle, faTrain, faTrainTram, faShip } from "@fortawesome/free-solid-svg-icons";
import { Mode } from "../../../types/types";
import "./Icons.css";

export function MultimodalIcon() {
    return (
        <div className="multimodal-icon">
            <div className="circle public-transport">
                <FontAwesomeIcon icon={faBusSimple} />
            </div>
            <div className="circle bicycle">
                <FontAwesomeIcon icon={faBicycle} />
            </div>
            <div className="circle walk">
                <FontAwesomeIcon icon={faPersonWalking} />
            </div>
        </div>
    );
}

export const modeIcons: {html: JSX.Element, value: Mode}[] = [{
        html: <MultimodalIcon />, 
        value: "transit,bicycle,walk"
    }, {
        html: 
            <div className="circle">
                <FontAwesomeIcon icon={faBusSimple}/>
            </div>, 
        value: "walk_transit"
    }, {
        html: 
            <div className="circle">
                <FontAwesomeIcon icon={faBicycle}/>
            </div>, 
        value: "bicycle"
    }, {
        html: 
            <div className="circle">
                <FontAwesomeIcon icon={faPersonWalking}/>
            </div>, 
        value: "foot"
    }
]

export const accuracyIcons: {html: JSX.Element, exact: boolean}[] = [{
        html: 
            <div className="accuracy-icon">
                <FontAwesomeIcon icon={faCrosshairs} className="accuracy" />
            </div>, 
        exact: true
    }, {
        html: 
            <div className="accuracy-icon">
                <FontAwesomeIcon icon={faCircle} className="accuracy" />
            </div>, 
        exact: false
    }
]

export const timelineIcons: {[mode: string]: JSX.Element} = {
    foot:
        <div className="timeline-icon">
            <FontAwesomeIcon icon={faPersonWalking} />
        </div>,
    bicycle:
        <div className="timeline-icon">
            <FontAwesomeIcon icon={faBicycle} />
        </div>,
    rail: 
        <div className="timeline-icon">
            <FontAwesomeIcon icon={faTrain} />
        </div>,
    bus:
        <div className="timeline-icon">
            <FontAwesomeIcon icon={faBusSimple} />
        </div>,
    tram:
        <div className="timeline-icon">
            <FontAwesomeIcon icon={faTrainTram} />
        </div>,
    trolleybus:
        <div className="timeline-icon">
            <FontAwesomeIcon icon={faBusSimple} />
        </div>,
    boat:
        <div className="timeline-icon">
            <FontAwesomeIcon icon={faShip} />
        </div>
}

/** End of file Icons.tsx */
