import assert from 'node:assert/strict'
import { after, before, describe, it } from 'node:test'

import {
  DISENO,
  cargarManifiesto,
  crearVisor,
  inyectar,
  rutaSegura,
  rutasDeBlobs,
  tarjeta,
} from './visor.mjs'

describe('utilidades', () => {
  it('mapea cada blob del manifiesto a su ilustración', () => {
    const blobs = rutasDeBlobs(cargarManifiesto())
    assert.equal(Object.keys(blobs).length, 14)
    assert.equal(blobs['22703e1a591f4d8613c14c97e2fab84d'], 'assets/Ilustraciones/bulto.svg')
  })

  it('no deja salir de la carpeta del prototipo', () => {
    assert.equal(rutaSegura(DISENO, '../../back/.env'), null)
    assert.equal(rutaSegura(DISENO, '%2e%2e/%2e%2e/README.md'), null)
    assert.ok(rutaSegura(DISENO, 'tokens.css').endsWith('tokens.css'))
  })

  it('inyecta tokens, estilos y utilidades al inicio del head', () => {
    const html = inyectar('<html><head><title>x</title></head></html>')
    assert.match(html, /^<html><head><link rel="stylesheet" href="\/ds\/tokens\.css">/)
    assert.ok(html.indexOf('bundle.js') < html.indexOf('<title>'))
  })

  it('lee la tarjeta @dsCard', () => {
    const t = tarjeta('<!-- @dsCard group="Web" height=800 width=1250 subtitle="Oficina" -->')
    assert.deepEqual(t, { grupo: 'Web', alto: '800', ancho: '1250', subtitulo: 'Oficina' })
  })
})

describe('servidor', () => {
  let servidor
  let base

  before(async () => {
    servidor = crearVisor()
    await new Promise((listo) => servidor.listen(0, listo))
    base = `http://localhost:${servidor.address().port}`
  })

  after(() => servidor.close())

  it('lista las 13 pantallas en el índice', async () => {
    const html = await (await fetch(`${base}/`)).text()
    assert.equal((html.match(/href="\/c\//g) ?? []).length, 13)
  })

  it('sirve una vista previa con los recursos inyectados', async () => {
    const r = await fetch(`${base}/c/Caseta`)
    assert.equal(r.status, 200)
    const html = await r.text()
    assert.match(html, /\/ds\/components\/bundle\.js/)
    assert.match(html, /<title>Caseta<\/title>/)
  })

  it('sirve ilustraciones por blob y recursos del sistema', async () => {
    const svg = await fetch(`${base}/_blob/22703e1a591f4d8613c14c97e2fab84d`)
    assert.equal(svg.status, 200)
    assert.equal(svg.headers.get('content-type'), 'image/svg+xml')
    assert.equal((await fetch(`${base}/ds/tokens.css`)).status, 200)
  })

  it('responde 404 a lo que no existe o sale del prototipo', async () => {
    assert.equal((await fetch(`${base}/c/NoExiste`)).status, 404)
    assert.equal((await fetch(`${base}/_blob/abc`)).status, 404)
    assert.equal((await fetch(`${base}/ds/%2e%2e/%2e%2e/back/.env.example`)).status, 404)
  })
})
