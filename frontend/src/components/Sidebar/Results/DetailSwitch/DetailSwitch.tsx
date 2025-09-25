/**
 * @file DetailSwitch.tsx
 * @brief Provides navigation between trip pattern details
 * @author Andrea Svitkova (xsvitka00)
 */

import { faAngleLeft, faAngleRight } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { IconButton } from "@mui/material";
import RadioButtonUncheckedIcon from '@mui/icons-material/RadioButtonUnchecked';
import RadioButtonCheckedIcon from '@mui/icons-material/RadioButtonChecked';
import "./DetailSwitch.css"

type DetailSwitchProps = {
  numOfPatterns: number;
  selectedTripPatternIndex: number;
  setSelectedTripPatternIndex: (value: number | ((prev: number) => number)) => void;
  setPublicLegIndex: (value: number) => void;
};

function DetailSwitch({
  numOfPatterns,
  selectedTripPatternIndex,
  setSelectedTripPatternIndex,
  setPublicLegIndex
}: DetailSwitchProps) {
  return (
    <div className="detail-switch">
      <IconButton
        className="detail-switch-arrow"
        onClick={() => {
          setSelectedTripPatternIndex((prev) =>
            prev > 0 ? prev - 1 : numOfPatterns - 1
          );
          setPublicLegIndex(-1);
        }
        }
      >
        <FontAwesomeIcon icon={faAngleLeft} />
      </IconButton>

      <div className="dots">
        {Array.from({ length: numOfPatterns }, (_, i) => (
          <IconButton key={i} onClick={() => {setSelectedTripPatternIndex(i); setPublicLegIndex(-1);}}>
            {i === selectedTripPatternIndex ? (
              <RadioButtonCheckedIcon className="dot"/>
            ) : (
              <RadioButtonUncheckedIcon className="dot"/>
            )}
          </IconButton>
        ))}
      </div>

      <IconButton
        className="detail-switch-arrow"
        onClick={() => {
          setSelectedTripPatternIndex((prev) =>
            prev < numOfPatterns - 1 ? prev + 1 : 0
          );
          setPublicLegIndex(-1);
          }
        }
      >
        <FontAwesomeIcon icon={faAngleRight} />
      </IconButton>
    </div>
  );
}

export default DetailSwitch;

/** End of file DetailSwitch.tsx */
