type Props = { size?: number; className?: string };

export default function HatchLogo({ size = 18, className = "" }: Props) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      aria-label="Hatch"
    >
      <defs>
        <linearGradient id="hatchg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#FFC857" />
          <stop offset="100%" stopColor="#FF7A45" />
        </linearGradient>
      </defs>
      {/* egg silhouette */}
      <path
        d="M12 2C7.5 2 4 8 4 13.5C4 18.2 7.6 22 12 22C16.4 22 20 18.2 20 13.5C20 8 16.5 2 12 2Z"
        fill="url(#hatchg)"
      />
      {/* crack */}
      <path
        d="M6.5 13L9 11L11 13L13.5 11.5L15.5 13.5L18 12.5"
        stroke="white"
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
