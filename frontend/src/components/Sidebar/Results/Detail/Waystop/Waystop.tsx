import "./Waystop.css";

type WaystopProps = {
    time: string;
    name: string | undefined;
};

function Waystop({
    time,
    name
} : WaystopProps) {
    return (
        <div className="waystop">
            <div className="waystop-detail">
                <span>
                    {time}
                </span>
                <span>
                    {name}
                </span>
            </div>
        </div>
    )
}

export default Waystop;
