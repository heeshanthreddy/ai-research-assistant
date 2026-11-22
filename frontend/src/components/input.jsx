// Reusable Input Field Component for ResearchForge Design System
export function Input({
    label,
    error,
    help,
    type = "text",
    placeholder = "",
    value,
    onChange,
    required = false,
    className = "",
    style = {},
    ...props
}) {
    return (
        <div style={{ display: "flex", flexDirection: "column", marginBottom: "12px", ...style }}>
            {label && (
                <label className="form-label">
                    {label} {required && <span style={{ color: "var(--rf-danger)" }}>*</span>}
                </label>
            )}
            <input
                type={type}
                placeholder={placeholder}
                value={value}
                onChange={onChange}
                required={required}
                className={className}
                {...props}
            />
            {help && <span className="form-help">{help}</span>}
            {error && <span className="error-text small" style={{ marginTop: "4px" }}>{error}</span>}
        </div>
    );
}

export default Input;
