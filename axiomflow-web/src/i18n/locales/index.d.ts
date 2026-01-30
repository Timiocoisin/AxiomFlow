// 类型定义：确保 TypeScript 能正确识别 JSON 导入
declare module '*.json' {
  const value: Record<string, any>;
  export default value;
}

