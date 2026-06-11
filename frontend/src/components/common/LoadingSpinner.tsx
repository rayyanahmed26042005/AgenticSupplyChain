export default function LoadingSpinner({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="loading-overlay">
      <div className="spinner" />
      <p style={{ fontSize: '0.9rem' }}>{message}</p>
    </div>
  );
}
