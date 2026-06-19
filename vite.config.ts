import { defineConfig, type Plugin } from 'vite'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'
import { readFileSync } from 'fs'
import { getMacroDefines } from './scripts/defines'
import featureFlagsPlugin from './scripts/vite-plugin-feature-flags'
import importMetaRequirePlugin from './scripts/vite-plugin-import-meta-require'

const projectRoot = dirname(fileURLToPath(import.meta.url))

const acknowledgedSideEffectPackages = [
  '@radix-ui/react-use-callback-ref',
  '@radix-ui/react-use-layout-effect',
  '@radix-ui/react-use-previous',
  '@radix-ui/react-primitive',
  '@radix-ui/react-focus-guards',
  '@radix-ui/react-focus-scope',
  '@radix-ui/react-portal',
  '@radix-ui/react-dismissable-layer',
  '@radix-ui/react-compose-refs',
  '@radix-ui/react-slot',
  '@radix-ui/react-collection',
  '@radix-ui/react-roving-focus',
  '@radix-ui/react-direction',
  '@radix-ui/react-visually-hidden',
  '@radix-ui/react-menu',
  '@radix-ui/react-popper',
  '@radix-ui/react-arrow',
  '@radix-ui/react-use-rect',
  '@radix-ui/react-use-size',
  '@radix-ui/react-id',
  'react-dom',
  'react',
]

const externalPackages = [
  'electron',
  'node:path',
  'node:url',
  'node:fs',
  'node:fs/promises',
  'node:os',
  'node:child_process',
  'node:stream',
  'node:buffer',
  'node:util',
  'node:events',
  'node:net',
  'node:http',
  'node:https',
  'node:crypto',
  'node:zlib',
  'node:readline',
  'node:process',
  'node:tty',
  'node:assert',
  'node:string_decoder',
  'node:punycode',
  '@nut-tree-fork/nut-js',
]

const conditionalExternalPackages = [
  'sharp',
  '@img/sharp-linux-arm64',
  '@img/sharp-linux-x64',
]

export default defineConfig(({ mode }) => ({
  test: {
    globals: true,
    environment: 'node',
    environmentOptions: {},
    exclude: ['**/*.test.ts.snap', 'node_modules/**'],
    setupFiles: ['./tests/vitest.setup.ts'],
    testTimeout: 15000,
    resolveSnapshotPath(testPath, snapshotExtension) {
      return testPath + snapshotExtension
    },
  },
  define: getMacroDefines(mode),
  plugins: [
    featureFlagsPlugin({ mode }),
    importMetaRequirePlugin(),
  ],
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: {
        main: resolve(projectRoot, 'src/main.tsx'),
      },
      onwarn(warning, defaultHandler) {
        const msg = warning.message
        const isOk =
          (warning.code === 'MODULE_LEVEL_DIRECTIVE' && msg.includes('use client')) ||
          (warning.code === 'SOURCEMAP_ERROR') ||
          (warning.code === 'CIRCULAR_DEPENDENCY') ||
          (warning.code === 'THIS_IS_UNDEFINED') ||
          (warning.code === 'INVALID_ANNOTATION' && msg.includes('@__PURE__'))
        if (isOk) return
        defaultHandler(warning)
      },
      output: {
        entryFileNames: '[name].js',
        chunkFileNames: '[name].js',
        assetFileNames: '[name].[ext]',
        format: 'esm',
        dir: 'dist',
        manualChunks: undefined,
        inlineDynamicImports: true,
      },
      external: [
        ...externalPackages,
        ...conditionalExternalPackages,
        (id) => {
          if (id.endsWith('.node')) return true
          return false
        },
      ],
      plugins: [
        {
          name: 'mark-side-effect-free',
          transform(code, id) {
            const isAcknowledgedSideEffectPackage = acknowledgedSideEffectPackages.some(
              (pkg) => id.includes(`node_modules/${pkg}`),
            )
            if (isAcknowledgedSideEffectPackage) {
              return {
                code: code.replace(/^\/\* #__PURE__ \*\//gm, ''),
                map: null,
              }
            }
          },
        } satisfies Plugin,
      ],
    },
  },
}))
