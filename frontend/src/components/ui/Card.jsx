// Card.jsx — a sheet of paper: off-white, hairline border, square corners, no shadow.
// Used as the content block across teacher, TA and student pages.

export default function Card({ children, className = "", ...props }) {
  return (
    <div className={`bg-paper-50 border border-paper-300 rounded-sm ${className}`} {...props}>
      {children}
    </div>
  );
}

// Section header with a hairline rule under it
Card.Header = function CardHeader({ children, className = "" }) {
  return <div className={`px-5 py-3 border-b border-paper-300 ${className}`}>{children}</div>;
};

Card.Body = function CardBody({ children, className = "" }) {
  return <div className={`px-5 py-4 ${className}`}>{children}</div>;
};

// Footer strip for actions, slightly darker paper
Card.Footer = function CardFooter({ children, className = "" }) {
  return <div className={`px-5 py-3 border-t border-paper-300 bg-paper-100 ${className}`}>{children}</div>;
};
