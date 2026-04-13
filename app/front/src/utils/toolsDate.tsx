export function formatDelay(minutes: number): string {
  if (minutes < 60) return `${minutes} min`
  const h = Math.floor(minutes / 60)
  const rem = minutes % 60
  return rem > 0 ? `${h}h ${rem} min` : `${h}h`
}

// const getNowFormatted = () => {
//   const now = new Date();
//   const offset = now.getTimezoneOffset();
//   const local = new Date(now.getTime() - offset * 60 * 1000);
//   return local.toISOString().slice(0, 16);
// };

export const getRoundedHourFormatted = () => {
  const now = new Date();

  if (now.getMinutes() < 30) {
    now.setMinutes(0, 0, 0);
  } else {
    now.setHours(now.getHours() + 1, 0, 0, 0);
  }

  const offset = now.getTimezoneOffset();
  const local = new Date(now.getTime() - offset * 60 * 1000);

  return local.toISOString().slice(0, 16);
};
