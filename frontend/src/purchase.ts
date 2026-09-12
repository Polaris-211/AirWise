/** 携程单程搜索：三字码必须小写。 */
export function ctripOnewayUrl(
  origin: string,
  destination: string,
  flightDate: string
): string {
  const o = origin.trim().toLowerCase();
  const d = destination.trim().toLowerCase();
  return `https://flights.ctrip.com/online/list/oneway-${o}-${d}?depdate=${flightDate}`;
}
