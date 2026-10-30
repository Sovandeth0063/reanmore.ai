import { Circle, Droplet, Minus, Plus, Snowflake, Wind, type LucideIcon } from 'lucide-react';

const ICON_RULES: Array<[RegExp, LucideIcon]> = [
  [/(solid|ice|cube|freez)/i, Snowflake],
  [/(liquid|water|melt)/i, Droplet],
  [/(gas|air|vapou?r|steam|boil|evapor)/i, Wind],
  [/(add|plus|sum|join|together|in all)/i, Plus],
  [/(subtract|minus|take away|left|remain)/i, Minus],
];

/**
 * Replaces decorative emoji with a real icon. Every answer option gets a
 * consistent leading icon; unknown options fall back to a neutral dot.
 */
export function OptionIcon({
  label,
  className = 'w-4 h-4 shrink-0',
}: {
  label: string;
  className?: string;
}) {
  const rule = ICON_RULES.find(([pattern]) => pattern.test(label));
  const Icon = rule ? rule[1] : Circle;
  return <Icon className={className} aria-hidden="true" />;
}
