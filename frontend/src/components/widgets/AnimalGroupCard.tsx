/**
 * AnimalGroupCard.tsx
 * Shows animal group info for science grouping exercises.
 */

interface Props {
  group: string;
  emoji: string;
}

const GROUP_FACTS: Record<string, string> = {
  bird:        'Birds have feathers and (usually) can fly.',
  mammal:      'Mammals have hair or fur and feed their young milk.',
  amphibian:   'Amphibians have moist skin and live on land AND in water.',
  reptile:     'Reptiles have dry scales.',
  fish:        'Fish have gills and live in water.',
  invertebrate:'Invertebrates do NOT have a backbone.',
};

export function AnimalGroupCard({ group, emoji }: Props) {
  const fact = GROUP_FACTS[group.toLowerCase()] ?? 'Think about what makes this group special.';
  return (
    <div className="w-full bg-white/70 rounded-2xl border-2 border-cyan-200 p-4 mb-3">
      <div className="flex items-center gap-3 mb-2">
        <span className="text-4xl">{emoji}</span>
        <div>
          <div className="font-black text-cyan-800 capitalize text-base">{group}</div>
          <div className="text-xs text-cyan-600">Animal group</div>
        </div>
      </div>
      <div className="bg-cyan-50 rounded-xl p-2 border border-cyan-200">
        <p className="text-xs text-cyan-700">💡 Clue: {fact}</p>
      </div>
      <p className="text-xs text-cyan-600 mt-2">What ONE feature is most important for this group?</p>
    </div>
  );
}

