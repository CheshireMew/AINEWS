import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const rootDir = path.dirname(fileURLToPath(import.meta.url))

function chunkByNodeModulePackage(id) {
  const normalized = id.split('\\').join('/')
  const marker = '/node_modules/'
  const index = normalized.lastIndexOf(marker)
  if (index === -1) {
    return null
  }
  const modulePath = normalized.slice(index + marker.length)
  const segments = modulePath.split('/')
  if (segments[0].startsWith('@')) {
    return `${segments[0].slice(1)}-${segments[1]}`
  }
  return segments[0]
}

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@shared-content-contract': path.resolve(rootDir, '../shared/content_contract.json'),
    },
  },
  server: {
    fs: {
      allow: [path.resolve(rootDir, '..')],
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) {
            return
          }
          if (id.includes('react') || id.includes('react-dom') || id.includes('react-router-dom')) {
            return 'react-vendor'
          }
          if (id.includes('@ant-design/icons')) {
            return 'antd-icons'
          }
          if (id.includes('antd/es/layout') || id.includes('antd/es/tabs') || id.includes('antd/es/card') || id.includes('antd/es/statistic') || id.includes('antd/es/segmented') || id.includes('antd/es/modal') || id.includes('antd/es/collapse')) {
            return 'antd-shell'
          }
          if (id.includes('antd/es/button') || id.includes('antd/es/space') || id.includes('antd/es/grid') || id.includes('antd/es/flex')) {
            return 'antd-layout-core'
          }
          if (id.includes('antd/es/style') || id.includes('antd/es/theme') || id.includes('antd/es/config-provider') || id.includes('antd/es/app') || id.includes('antd/es/locale') || id.includes('@ant-design/cssinjs') || id.includes('@ant-design/colors') || id.includes('@ant-design/fast-color') || id.includes('@ant-design/cssinjs-utils')) {
            return 'antd-runtime'
          }
          if (id.includes('antd/es/table') || id.includes('antd/es/pagination')) {
            return 'antd-table'
          }
          if (id.includes('antd/es/form') || id.includes('antd/es/input') || id.includes('antd/es/select') || id.includes('antd/es/checkbox')) {
            return 'antd-form'
          }
          if (id.includes('antd/es/date-picker') || id.includes('antd/es/time-picker') || id.includes('antd/es/calendar') || id.includes('rc-picker')) {
            return 'antd-picker'
          }
          if (id.includes('rc-table') || id.includes('rc-pagination') || id.includes('rc-resize-observer') || id.includes('rc-virtual-list')) {
            return 'antd-table-core'
          }
          if (id.includes('rc-field-form') || id.includes('rc-select') || id.includes('rc-input') || id.includes('rc-textarea') || id.includes('rc-checkbox') || id.includes('rc-switch') || id.includes('rc-util')) {
            return 'antd-form-core'
          }
          if (id.includes('rc-menu') || id.includes('rc-dropdown') || id.includes('rc-overflow') || id.includes('rc-trigger') || id.includes('rc-tooltip') || id.includes('@rc-component/trigger') || id.includes('@rc-component/portal')) {
            return 'antd-overlay'
          }
          if (id.includes('rc-tree') || id.includes('antd/es/tree') || id.includes('antd/es/cascader')) {
            return 'antd-tree'
          }
          if (id.includes('antd/es/message') || id.includes('antd/es/notification') || id.includes('antd/es/progress') || id.includes('antd/es/result') || id.includes('antd/es/spin') || id.includes('antd/es/alert') || id.includes('antd/es/tour')) {
            return 'antd-feedback'
          }
          if (id.includes('antd/es/upload') || id.includes('antd/es/image') || id.includes('antd/es/avatar') || id.includes('antd/es/badge') || id.includes('antd/es/breadcrumb') || id.includes('antd/es/steps') || id.includes('antd/es/timeline') || id.includes('antd/es/collapse') || id.includes('antd/es/drawer') || id.includes('antd/es/anchor') || id.includes('antd/es/affix') || id.includes('antd/es/watermark') || id.includes('antd/es/mentions')) {
            return 'antd-misc'
          }
          if (id.includes('antd') || id.includes('rc-') || id.includes('@rc-component')) {
            const pkg = chunkByNodeModulePackage(id)
            if (pkg === 'rc-component-mini-decimal') {
              return 'ui-antd'
            }
            return pkg ? `ui-${pkg}` : 'antd-core'
          }
          if (id.includes('@phosphor-icons') || id.includes('react-icons')) {
            return 'icons-vendor'
          }
        },
      },
    },
  },
})
