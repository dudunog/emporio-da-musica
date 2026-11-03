const ROSETTE_RINGS = [
  { radius: 150, strokeWidth: 1, dashArray: undefined },
  { radius: 166, strokeWidth: 10, dashArray: "2 6" },
  { radius: 182, strokeWidth: 1, dashArray: undefined },
  { radius: 196, strokeWidth: 1, dashArray: undefined },
  { radius: 228, strokeWidth: 44, dashArray: "1 13" },
  { radius: 260, strokeWidth: 1, dashArray: undefined },
  { radius: 274, strokeWidth: 1, dashArray: undefined },
  { radius: 290, strokeWidth: 10, dashArray: "2 6" },
  { radius: 306, strokeWidth: 1, dashArray: undefined },
];

export function SoundholeOrnament() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 640 640"
      fill="none"
      className="pointer-events-none absolute -right-ornament-offset -bottom-ornament-offset size-ornament stroke-ornament in-[main:has([role=log]>:nth-child(2))]:ornament-in-conversation"
    >
      {ROSETTE_RINGS.map(({ radius, strokeWidth, dashArray }) => (
        <circle key={radius} cx="320" cy="320" r={radius} strokeWidth={strokeWidth} strokeDasharray={dashArray} />
      ))}
    </svg>
  );
}
