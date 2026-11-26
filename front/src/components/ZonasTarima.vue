<script setup>
defineOptions({
  name: 'ZonasTarima',
})
</script>

<template>
  <div class="zs">
    <div style="background-color: var(--pallet-heavy)">
      Caja roja<small>Pesado · ≥ 15 kg · abajo</small>
    </div>
    <div style="background-color: var(--pallet-mid); color: #3a2300">
      Caja naranja<small>Intermedio · 7–15 kg · en medio</small>
    </div>
    <div style="background-color: var(--pallet-light)">
      Caja verde<small>Ligero · &lt; 7 kg · arriba</small>
    </div>
  </div>
</template>

<style>
.zs {
  display: flex;
  gap: 10px;
}
.zs div {
  flex: 1;
  border-radius: 14px;
  padding: 12px;
  color: #fff;
  font-weight: 600;
  background-image:
    linear-gradient(rgba(0, 0, 0, 0.14) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 0, 0, 0.14) 1px, transparent 1px);
  background-size: 16px 16px;
}
.zs small {
  display: block;
  font-weight: 500;
  opacity: 0.95;
}
</style>
