import InfoIcon from '@mui/icons-material/Info';
import "./Information.css"

type InformationProps = {
    setShowInfo: (value: boolean) => void;
}

function Information({
    setShowInfo
} : InformationProps) {
    return (
        <button 
            className={"controls-button " + "controls-info"}
            onClick={() => setShowInfo(true)} 
            type="button"
            tabIndex={-1}
        >
            <InfoIcon sx={{ color: 'var(--color-text-primary)' }} />
        </button>
    );
}

export default Information;

/** End of file Information.tsx */
