<script setup>
import { ref } from 'vue'
import BotonBase from '@/components/BotonBase.vue'
import Chip from '@/components/Chip.vue'
import CampoTexto from '@/components/CampoTexto.vue'
import Segmentado from '@/components/Segmentado.vue'
import BarraAvance from '@/components/BarraAvance.vue'
import ZonasTarima from '@/components/ZonasTarima.vue'

defineOptions({
  name: 'ElementosView',
})

const usuario = ref('')
const modo = ref('in')

const opcionesSegmentado = [
  { valor: 'in', etiqueta: 'Entradas', icono: 'login', iconoTamano: 16 },
  { valor: 'out', etiqueta: 'Salidas', icono: 'exit', iconoTamano: 16 },
]
</script>

<template>
  <div class="stage">
    <div id="el" class="el">
      <div class="card">
        <div class="t-over" style="margin-bottom: 12px">Botones</div>
        <div class="row">
          <BotonBase variante="primary" icono="scan" :icono-tamano="20">Escanear bulto</BotonBase>
          <BotonBase variante="soft" icono-derecha="down" :icono-tamano="18">Ver más </BotonBase>
          <BotonBase variante="line" icono="download" :icono-tamano="18">PDF</BotonBase>
          <BotonBase variante="danger" icono="alert" :icono-tamano="18">Reportar</BotonBase>
          <BotonBase variante="primary" disabled>Relación</BotonBase>
        </div>
      </div>

      <div class="card">
        <div class="t-over" style="margin-bottom: 12px">Estados</div>
        <div class="row" style="gap: 8px">
          <Chip punto>En andén</Chip>
          <Chip variante="ok" icono="check" :icono-tamano="14" :icono-grosor="2.4">Recibido</Chip>
          <Chip variante="warn" icono="clock" :icono-tamano="14" :icono-grosor="2">Faltan 7</Chip>
          <Chip variante="bad" icono="x" :icono-tamano="14" :icono-grosor="2.4">Excedente</Chip>
          <Chip variante="mute">En rack</Chip>
        </div>
      </div>

      <div class="card">
        <div class="t-over" style="margin-bottom: 12px">Campos</div>
        <CampoTexto
          v-model="usuario"
          icono="user"
          placeholder="Usuario"
          style="margin-bottom: 10px"
        />
        <Segmentado v-model="modo" :opciones="opcionesSegmentado" />
      </div>

      <div class="card">
        <div class="t-over" style="margin-bottom: 12px">Progreso</div>
        <BarraAvance
          etiqueta="Peso de tarima"
          :valor="567"
          :tope="1000"
          unidad="kg"
          estilo-barra="margin: 6px 0 14px"
        />
        <BarraAvance
          etiqueta="Tortón · regla 90%"
          :valor="94"
          :tope="100"
          variante="ok"
          texto-valor="94%"
          color-valor="var(--success)"
          estilo-barra="margin-top: 6px"
        />
      </div>

      <div class="card" style="grid-column: 1 / -1">
        <div class="t-over" style="margin-bottom: 12px">
          Cajas de la tarima (por peso del bulto)
        </div>
        <ZonasTarima />
      </div>
    </div>
  </div>
</template>

<style>
.el {
  width: 960px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.el .card {
  padding: 18px;
}
.el .row {
  flex-wrap: wrap;
}
</style>
