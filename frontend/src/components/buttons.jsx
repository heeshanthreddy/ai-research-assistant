// Reusable Button Component for ResearchForge Design System
export function Button({
    children,
    variant = "primary", // primary, secondary, danger, link
    disabled = false,
    onClick,
    type = "button",
    style = {},
    className = "",
    ...props
}) {
    const variantClass = variant === "primary" ? "" : variant;
    return (
        <button
            type={type}
            disabled={disabled}
            onClick={onClick}
            className={`${variantClass} ${className}`.trim()}
            style={style}
            {...props}
        >
            {children}
        </button>
    );
}

export default Button;
