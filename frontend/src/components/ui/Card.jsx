// Card.jsx — white rounded container with soft shadow.
// Used as the primary content block across teacher and student pages.

export default function Card({ children, className = "", ...props }) {
  return (
    <div
      className={`bg-white rounded-xl shadow-sm border border-gray-100 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

// Convenience sub-components to keep card section spacing consistent
Card.Header = function CardHeader({ children, className = "" }) {
  return <div className={`px-6 py-4 border-b border-gray-100 ${className}`}>{children}</div>;
};

Card.Body = function CardBody({ children, className = "" }) {
  return <div className={`px-6 py-4 ${className}`}>{children}</div>;
};

Card.Footer = function CardFooter({ children, className = "" }) {
  return <div className={`px-6 py-4 border-t border-gray-100 bg-gray-50 rounded-b-xl ${className}`}>{children}</div>;
};
