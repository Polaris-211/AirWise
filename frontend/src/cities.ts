/** 城市（航站）数据，用于搜索式选择 */
export interface City {
  /** 中文名 */
  name: string;
  /** 拼音，全小写 */
  pinyin: string;
  /** 城市三字码，下单查询用 */
  code: string;
  /** 机场名 */
  airport: string;
  /** 机场三字码 */
  airportCode: string;
}

/** 内置主要城市，按常用度大致排序 */
export const CITIES: City[] = [
  { name: "北京", pinyin: "beijing", code: "BJS", airport: "首都国际机场", airportCode: "PEK" },
  { name: "上海", pinyin: "shanghai", code: "SHA", airport: "虹桥国际机场", airportCode: "SHA" },
  { name: "广州", pinyin: "guangzhou", code: "CAN", airport: "白云国际机场", airportCode: "CAN" },
  { name: "深圳", pinyin: "shenzhen", code: "SZX", airport: "宝安国际机场", airportCode: "SZX" },
  { name: "成都", pinyin: "chengdu", code: "CTU", airport: "双流国际机场", airportCode: "CTU" },
  { name: "成都天府", pinyin: "chengdutianfu", code: "TFU", airport: "天府国际机场", airportCode: "TFU" },
  { name: "杭州", pinyin: "hangzhou", code: "HGH", airport: "萧山国际机场", airportCode: "HGH" },
  { name: "西安", pinyin: "xian sia", code: "XIY", airport: "咸阳国际机场", airportCode: "XIY" },
  { name: "重庆", pinyin: "chongqing", code: "CKG", airport: "江北国际机场", airportCode: "CKG" },
  { name: "昆明", pinyin: "kunming", code: "KMG", airport: "长水国际机场", airportCode: "KMG" },
  { name: "厦门", pinyin: "xiamen", code: "XMN", airport: "高崎国际机场", airportCode: "XMN" },
  { name: "南京", pinyin: "nanjing", code: "NKG", airport: "禄口国际机场", airportCode: "NKG" },
  { name: "武汉", pinyin: "wuhan", code: "WUH", airport: "天河国际机场", airportCode: "WUH" },
  { name: "青岛", pinyin: "qingdao", code: "TAO", airport: "胶东国际机场", airportCode: "TAO" },
  { name: "长沙", pinyin: "changsha", code: "CSX", airport: "黄花国际机场", airportCode: "CSX" },
  { name: "郑州", pinyin: "zhengzhou", code: "CGO", airport: "新郑国际机场", airportCode: "CGO" },
  { name: "天津", pinyin: "tianjin", code: "TSN", airport: "滨海国际机场", airportCode: "TSN" },
  { name: "哈尔滨", pinyin: "haerbin", code: "HRB", airport: "太平国际机场", airportCode: "HRB" },
  { name: "三亚", pinyin: "sanya", code: "SYX", airport: "凤凰国际机场", airportCode: "SYX" },
  { name: "乌鲁木齐", pinyin: "wulumuqi", code: "URC", airport: "天山国际机场", airportCode: "URC" },
  { name: "沈阳", pinyin: "shenyang", code: "SHE", airport: "桃仙国际机场", airportCode: "SHE" },
  { name: "大连", pinyin: "dalian", code: "DLC", airport: "周水子国际机场", airportCode: "DLC" },
  { name: "福州", pinyin: "fuzhou", code: "FOC", airport: "长乐国际机场", airportCode: "FOC" },
  { name: "贵阳", pinyin: "guiyang", code: "KWE", airport: "龙洞堡国际机场", airportCode: "KWE" },
  { name: "南宁", pinyin: "nanning", code: "NNG", airport: "吴圩国际机场", airportCode: "NNG" },
  { name: "海口", pinyin: "haikou", code: "HAK", airport: "美兰国际机场", airportCode: "HAK" },
  { name: "兰州", pinyin: "lanzhou", code: "LHW", airport: "中川国际机场", airportCode: "LHW" },
  { name: "太原", pinyin: "taiyuan", code: "TYN", airport: "武宿国际机场", airportCode: "TYN" },
  { name: "合肥", pinyin: "hefei", code: "HFE", airport: "新桥国际机场", airportCode: "HFE" },
  { name: "济南", pinyin: "jinan", code: "TNA", airport: "遥墙国际机场", airportCode: "TNA" },
  { name: "拉萨", pinyin: "lasa", code: "LXA", airport: "贡嘎国际机场", airportCode: "LXA" },
  // 克拉玛依无直达合肥的航线，用于演示中转方案
  { name: "克拉玛依", pinyin: "kelamayi", code: "KRY", airport: "古海机场", airportCode: "KRY" },
];

/** 旧城市码 → 现行查询码 */
const CITY_ALIASES: Record<string, string> = { SIA: "XIY" };

/**
 * 按关键词匹配城市：中文名、拼音、三字码、机场名、机场代码都可命中。
 * 前缀匹配排在包含匹配之前，方便直接回车选中。
 */
export function searchCities(keyword: string, limit = 8): City[] {
  const q = keyword.trim().toLowerCase();
  if (!q) return CITIES.slice(0, limit);

  const prefix: City[] = [];
  const contains: City[] = [];

  for (const city of CITIES) {
    const fields = [
      city.name,
      city.pinyin,
      city.code.toLowerCase(),
      city.airport,
      city.airportCode.toLowerCase(),
    ];
    if (fields.some((f) => f.startsWith(q))) {
      prefix.push(city);
    } else if (fields.some((f) => f.includes(q))) {
      contains.push(city);
    }
  }

  return [...prefix, ...contains].slice(0, limit);
}

/** 按三字码找城市，用于显示中文名 */
export function findCityByCode(code: string): City | undefined {
  const raw = code.trim().toUpperCase();
  const c = CITY_ALIASES[raw] ?? raw;
  return CITIES.find((city) => city.code === c || city.airportCode === c);
}
