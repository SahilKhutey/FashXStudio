export const motion = {
  duration: {
    instant: 0,
    fast: 120,
    normal: 200,
    slow: 320,
  },

  feedback: {
    pressScale: 0.98,
    disabledOpacity: 0.45,
  },
} as const;

export type MotionDuration =
  (typeof motion.duration)[keyof typeof motion.duration];
