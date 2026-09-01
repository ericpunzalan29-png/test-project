import { motion } from "motion/react";

const ORBIT_SIZE = "clamp(220px, 44vw, 560px)";

function IconStethoscope({ className }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M6 3v4a3 3 0 0 0 6 0V3" />
      <path d="M9 10v3a4 4 0 0 0 4 4h1" />
      <circle cx="17" cy="17.5" r="2.3" />
    </svg>
  );
}

function IconSyringe({ className }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <g transform="rotate(-45 12 12)">
        <line x1="3" y1="12" x2="5" y2="12" />
        <line x1="5" y1="9" x2="5" y2="15" />
        <rect x="5" y="9.5" width="9" height="5" rx="1" />
        <line x1="7.5" y1="9.5" x2="7.5" y2="14.5" />
        <line x1="10" y1="9.5" x2="10" y2="14.5" />
        <line x1="12.5" y1="9.5" x2="12.5" y2="14.5" />
        <line x1="14" y1="12" x2="17" y2="12" />
        <line x1="17" y1="12" x2="21" y2="8" />
      </g>
    </svg>
  );
}

function IconPulse({ className }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M2 12h4l2-7 3 14 2-9 2 5h7" />
    </svg>
  );
}

function IconPill({ className }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <g transform="rotate(45 12 12)">
        <rect x="3" y="8" width="18" height="8" rx="4" />
        <line x1="12" y1="8" x2="12" y2="16" />
      </g>
    </svg>
  );
}

function IconMedicalCross({ className }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M9 3h6v6h6v6h-6v6H9v-6H3V9h6V3z" />
    </svg>
  );
}

const ORBIT_ICONS = [
  { Icon: IconStethoscope, angle: -90, tiltY: -18 },
  { Icon: IconSyringe, angle: -18, tiltY: 16 },
  { Icon: IconPulse, angle: 54, tiltY: -14 },
  { Icon: IconPill, angle: 126, tiltY: 20 },
  { Icon: IconMedicalCross, angle: 198, tiltY: -16 },
];

export default function HeroOrbitBackground({ className = "" }) {
  return (
    <div
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 z-0 flex items-center justify-center overflow-hidden ${className}`}
      style={{ perspective: "1000px" }}
    >
      <motion.div
        className="relative text-slate-400"
        style={{ width: ORBIT_SIZE, height: ORBIT_SIZE, transformStyle: "preserve-3d" }}
        animate={{ rotate: 360 }}
        transition={{ duration: 26, ease: "linear", repeat: Infinity }}
      >
        {ORBIT_ICONS.map(({ Icon, angle, tiltY }, i) => (
          <div
            key={i}
            className="absolute left-1/2 top-1/2 opacity-20"
            style={{
              transform: `translate(-50%, -50%) rotate(${angle}deg) translateX(calc(${ORBIT_SIZE} / 2)) rotate(${-angle}deg)`,
            }}
          >
            <div style={{ transform: `rotateY(${tiltY}deg)`, transformStyle: "preserve-3d" }}>
              <Icon className="h-8 w-8 md:h-11 md:w-11" />
            </div>
          </div>
        ))}
      </motion.div>
    </div>
  );
}
