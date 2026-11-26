import { readFileSync } from 'node:fs'
import { describe, it, expect } from 'vitest'

const tokensCss = readFileSync('src/styles/tokens.css', 'utf8')
const fontsCss = readFileSync('src/styles/fonts.css', 'utf8')
const mainJs = readFileSync('src/main.js', 'utf8')
const ilustraciones = import.meta.glob('@/assets/ilustraciones/*.svg')
const fuentes = import.meta.glob('@/assets/fonts/*.woff2')
const cssAssets = import.meta.glob('@/assets/*.css')

describe('FE-01 · Tokens, tipografía e ilustraciones', () => {
  it('incluye los tokens del prototipo sin modificaciones y los carga en main.js', () => {
    expect(tokensCss).toContain('--brand-600: #1f5fd6;')
    expect(tokensCss).toContain('--ink: #0f1f3d;')
    expect(tokensCss).toContain('--pallet-heavy: #d13438;')
    expect(tokensCss).toContain('--font-sans: Poppins, system-ui, sans-serif;')
    expect(tokensCss).toContain('.display {')
    expect(tokensCss).toContain('.overline {')
    expect(mainJs).toContain("import './styles/tokens.css'")
  })

  it('sirve Poppins (400, 500, 600, 700) de forma local sin Google Fonts', () => {
    expect(fontsCss).not.toContain('fonts.googleapis.com')
    expect(fontsCss).toContain('font-weight: 400;')
    expect(fontsCss).toContain('font-weight: 500;')
    expect(fontsCss).toContain('font-weight: 600;')
    expect(fontsCss).toContain('font-weight: 700;')
    expect(mainJs).toContain("import './styles/fonts.css'")
    const archivosFuentes = Object.keys(fuentes)
      .map((ruta) => ruta.split('/').pop())
      .sort()
    expect(archivosFuentes).toEqual([
      'poppins-400.woff2',
      'poppins-500.woff2',
      'poppins-600.woff2',
      'poppins-700.woff2',
    ])
  })

  it('copia las 14 ilustraciones SVG del prototipo', () => {
    const nombres = Object.keys(ilustraciones)
      .map((ruta) => ruta.split('/').pop())
      .sort()
    expect(nombres).toEqual([
      'agenda.svg',
      'anden.svg',
      'bulto.svg',
      'caseta.svg',
      'cedis.svg',
      'clips.svg',
      'datos.svg',
      'embarque.svg',
      'hojas.svg',
      'impresora.svg',
      'lapices.svg',
      'login.svg',
      'recibo.svg',
      'sucursal.svg',
    ])
  })

  it('elimina base.css y main.css de src/assets', () => {
    expect(Object.keys(cssAssets)).toEqual([])
  })
})
