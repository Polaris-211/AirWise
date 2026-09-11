/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      // 苹果风格极简色板：黑白灰 + 单一点缀蓝
      colors: {
        ink: "#1d1d1f", // 主标题
        subtle: "#86868b", // 次要文字
        hairline: "#d2d2d7", // 极细分隔线
        canvas: "#f5f5f7", // 浅背景 / 输入框底色
        accent: "#0071e3", // 唯一点缀色
        "accent-dark": "#0077ed",
        danger: "#d70015", // 错误提示文字
      },
      fontFamily: {
        sans: [
          "-apple-system",
          "BlinkMacSystemFont",
          "SF Pro Display",
          "SF Pro Text",
          "Inter",
          "Segoe UI",
          "PingFang SC",
          "Microsoft YaHei",
          "sans-serif",
        ],
      },
      letterSpacing: {
        tighter: "-0.02em",
      },
      borderRadius: {
        card: "20px", // 卡片
        control: "12px", // 输入框
        button: "14px", // 按钮
      },
      // 柔和阴影，卡片不靠边框区分层次
      boxShadow: {
        card: "0 2px 24px rgba(0,0,0,0.06)",
        "card-hover": "0 6px 32px rgba(0,0,0,0.10)",
        bar: "0 1px 0 rgba(0,0,0,0.04)",
      },
      transitionTimingFunction: {
        // key 会自动带上 ease- 前缀，这里写 out-soft 才生成 .ease-out-soft
        "out-soft": "cubic-bezier(0.25, 0.46, 0.45, 0.94)",
      },
      transitionDuration: {
        250: "250ms",
      },
      keyframes: {
        // 淡入 + 轻微上浮
        "rise-in": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        // 提示条从顶部滑入
        "slide-down": {
          "0%": { opacity: "0", transform: "translateY(-12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        // 状态点呼吸：极轻微的明暗起伏
        breathe: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.5" },
        },
        // 状态点外扩光晕，一圈淡出
        halo: {
          "0%": { transform: "scale(1)", opacity: "0.35" },
          "70%, 100%": { transform: "scale(2.4)", opacity: "0" },
        },
      },
      animation: {
        "rise-in": "rise-in 250ms cubic-bezier(0.25, 0.46, 0.45, 0.94) both",
        "slide-down":
          "slide-down 250ms cubic-bezier(0.25, 0.46, 0.45, 0.94) both",
        breathe: "breathe 2.6s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        halo: "halo 2.6s cubic-bezier(0.25, 0.46, 0.45, 0.94) infinite",
      },
    },
  },
  plugins: [],
};
