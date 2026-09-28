import React, { useState } from 'react';
import { TunsayState } from '../types';

/* Only these 6 mascot images are available in src/assets/.
   All 11 states map to the closest matching available image.  */
import lionWaving      from '../assets/lion_waving.png';
import lionConfused    from '../assets/lion_confused.png';
import lionListening   from '../assets/lion_listening.png';
import lionHappy       from '../assets/lion_happy.png';
import lionJumping     from '../assets/lion_jumping.png';
import lionWinking     from '../assets/lion_winking.png';

interface TunsayAvatarProps {
  state?: TunsayState;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showBadge?: boolean;
  className?: string;
  onClick?: () => void;
  speechBubbleText?: string;
}

/* Map 11 states → 6 available images */
const STATE_IMAGE: Record<TunsayState, string> = {
  idle:        lionListening,  // calm sitting smile
  waving:      lionWaving,     // waving paw
  thinking:    lionConfused,    // paw on chin, pondering
  listening:   lionListening,   // gentle attentive smile
  explaining:  lionHappy,       // lightbulb = idea moment
  encouraging: lionWinking,     // friendly supportive wink
  happy:       lionHappy,       // lightbulb moment
  celebrating: lionJumping,     // jumping with stars
  jumping:     lionJumping,     // jumping with stars
  confused:    lionConfused,    // question mark, curious
  sleeping:    lionListening,   // calm resting fallback
};

const STATE_ANIM: Record<TunsayState, string> = {
  idle:        'animate-lion-idle',
  waving:      'animate-lion-wave',
  thinking:    'animate-lion-think',
  listening:   'animate-lion-listen',
  explaining:  'animate-lion-nod',
  encouraging: 'animate-lion-encourage',
  happy:       'animate-lion-happy',
  celebrating: 'animate-lion-celebrate',
  jumping:     'animate-lion-jump',
  confused:    'animate-lion-confused',
  sleeping:    'animate-lion-sleep',
};

const BADGE_LABEL: Record<TunsayState, string> = {
  idle:        'ReanMore WEG',
  waving:      'Hello!',
  thinking:    'Thinking...',
  listening:   'Listening...',
  explaining:  'Explaining...',
  encouraging: 'Encouraging!',
  happy:       'Yay!',
  celebrating: 'Done!',
  jumping:     'Amazing!',
  confused:    'Hmm...',
  sleeping:    'Zzz...',
};

export const ReanMoreAvatar: React.FC<TunsayAvatarProps> = ({
  state = 'idle',
  size = 'md',
  showBadge = true,
  className = '',
  onClick,
  speechBubbleText
}) => {
  const [isShaking, setIsShaking] = useState(false);

  const dimensions = {
    sm: 'w-10 h-10 sm:w-12 sm:h-12',
    md: 'w-16 h-16 sm:w-20 sm:h-20',
    lg: 'w-24 h-24 sm:w-28 sm:h-28 lg:w-32 lg:h-32',
    xl: 'w-28 h-28 sm:w-36 sm:h-36 lg:w-44 lg:h-44',
  }[size];

  const handleClick = () => {
    setIsShaking(true);
    setTimeout(() => setIsShaking(false), 700);
    if (onClick) onClick();
  };

  const imgSrc   = STATE_IMAGE[state] ?? lionListening;
  const animCls  = isShaking ? 'animate-lion-shake' : (STATE_ANIM[state] ?? 'animate-lion-idle');

  return (
    <div className={`relative inline-flex flex-col items-center select-none ${className}`}>

      {/* Speech bubble */}
      {speechBubbleText && (
        <div className="absolute -top-12 bg-white text-[#2E2A26] px-3 py-1.5 rounded-2xl shadow-md border-2 border-[#4C9A6A]/20 text-xs sm:text-sm font-semibold whitespace-nowrap animate-bounce z-20">
          {speechBubbleText}
          <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[8px] border-t-white" />
        </div>
      )}

      {/* Lion image — swaps per state */}
      <div
        onClick={handleClick}
        className={`${dimensions} cursor-pointer relative`}
        title="Tap ReanMore!"
      >
        <img
          key={state}
          src={imgSrc}
          alt={`ReanMore - ${state}`}
          className={`w-full h-full object-contain drop-shadow-lg transition-opacity duration-300 ${animCls}`}
          draggable={false}
        />
      </div>

      {/* Badge */}
      {showBadge && (
        <span className="mt-1 px-2 py-0.5 bg-[#4C9A6A]/10 text-[#357A4E] text-[11px] font-extrabold rounded-full tracking-wide uppercase border border-[#4C9A6A]/20">
          {BADGE_LABEL[state] ?? 'ReanMore WEG'}
        </span>
      )}
    </div>
  );
};

export const TunsayAvatar = ReanMoreAvatar;
