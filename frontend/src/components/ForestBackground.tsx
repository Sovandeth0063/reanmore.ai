import React, { useMemo } from 'react';
import forestBgImg from '../assets/forest_bg.jpg';

interface ForestBackgroundProps {
  activeTab?: 'home' | 'chat' | 'profile' | 'report';
}

export const ForestBackground: React.FC<ForestBackgroundProps> = ({ activeTab = 'home' }) => {
  const isChat = activeTab === 'chat';

  // Gentle ambient sunlight motes / fireflies
  const sparkles = useMemo(() => [
    { id: 1, top: '15%', left: '10%', size: 6, delay: '0s', duration: '5s' },
    { id: 2, top: '22%', left: '85%', size: 8, delay: '1.5s', duration: '6s' },
    { id: 3, top: '48%', left: '15%', size: 5, delay: '0.8s', duration: '4.5s' },
    { id: 4, top: '65%', left: '88%', size: 7, delay: '2.2s', duration: '5.2s' },
    { id: 5, top: '35%', left: '52%', size: 6, delay: '1.1s', duration: '5.8s' },
  ], []);

  return (
    <div
      className="fixed inset-0 pointer-events-none overflow-hidden select-none z-0"
      aria-hidden="true"
    >
      {/* ── High-Resolution Illustrated Jungle / Forest Backdrop ── */}
      <img
        src={forestBgImg}
        alt=""
        className="w-full h-full object-cover object-bottom transition-opacity duration-700"
      />

      {/* ── Atmospheric Veil for Flawless Readability on Mobile & Desktop ── */}
      <div
        className={`absolute inset-0 transition-all duration-500 ${
          isChat
            ? 'bg-gradient-to-b from-[#E8F5E9]/88 via-[#E8F5E9]/80 to-[#E8F5E9]/92 backdrop-blur-[2px]'
            : 'bg-gradient-to-b from-[#E8F5E9]/55 via-[#E8F5E9]/35 to-[#E8F5E9]/65'
        }`}
      />

      {/* ── Warm Sunlight Glow ── */}
      <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-[600px] max-w-full h-[320px] bg-gradient-to-b from-[#FFF9D2]/35 via-[#FFEAA7]/10 to-transparent blur-3xl pointer-events-none" />

      {/* ── Gentle Sparkling Light Motes ── */}
      {sparkles.map((sp) => (
        <div
          key={sp.id}
          className="absolute rounded-full bg-[#FFF9C4] shadow-[0_0_8px_2px_#FEE082] animate-firefly-glow pointer-events-none"
          style={{
            top: sp.top,
            left: sp.left,
            width: `${sp.size}px`,
            height: `${sp.size}px`,
            animationDelay: sp.delay,
            animationDuration: sp.duration,
          }}
        />
      ))}
    </div>
  );
};
