/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 阿里云 Aliplayer 全局类型声明
declare interface Window {
  Aliplayer: any
}
