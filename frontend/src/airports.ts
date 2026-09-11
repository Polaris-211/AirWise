/**
 * 机场三字码 -> 中文名。
 * 新增机场在下表加一行即可，查不到时只显示三字码。
 */
export const AIRPORT_NAMES: Record<string, string> = {
  PEK: "首都国际",
  PKX: "大兴国际",
  SHA: "虹桥国际",
  PVG: "浦东国际",
  CAN: "白云国际",
  SZX: "宝安国际",
  CTU: "双流国际",
  TFU: "天府国际",
};

/** 拼成「三字码 + 中文名」的展示文案 */
export function airportLabel(code: string | null | undefined): string {
  if (!code) return "—";
  const upper = code.toUpperCase();
  const name = AIRPORT_NAMES[upper];
  return name ? `${upper} ${name}` : upper;
}
