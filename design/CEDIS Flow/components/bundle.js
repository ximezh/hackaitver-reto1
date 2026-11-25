/* CEDIS Flow — utilidades compartidas: íconos, ilustraciones, datos de ejemplo y ayudas. Sin React. */
(function () {
  var P = {
    home: 'M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z',
    truck: 'M2 6h11v10H2zM13 10h4l4 4v2h-8zM6.5 19.5a1.8 1.8 0 1 0 0-.01M17.5 19.5a1.8 1.8 0 1 0 0-.01',
    box: 'M21 8l-9-5-9 5v8l9 5 9-5zM3 8l9 5 9-5M12 13v8',
    scan: 'M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3M4 12h16',
    qr: 'M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h2v2h-2zM18 14h2M14 18v2M18 18h2v2',
    calendar: 'M4 6h16v14H4zM4 10h16M8 3v4M16 3v4',
    clock: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7v5l3 2',
    check: 'M5 12.5l4.5 4.5L19 7.5',
    x: 'M6 6l12 12M18 6L6 18',
    alert: 'M12 3l10 18H2zM12 10v4M12 17.5v.01',
    user: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21a8 8 0 0 1 16 0',
    lock: 'M5 11h14v10H5zM8 11V7a4 4 0 0 1 8 0v4',
    eye: 'M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
    search: 'M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14zM20 20l-4-4',
    plus: 'M12 5v14M5 12h14',
    edit: 'M4 20h4L19 9l-4-4L4 16zM14 6l4 4',
    trash: 'M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13',
    right: 'M9 6l6 6-6 6', left: 'M15 6l-6 6 6 6', down: 'M6 9l6 6 6-6', up: 'M6 15l6-6 6 6',
    logout: 'M15 4h4v16h-4M10 8l-4 4 4 4M6 12h10',
    history: 'M3 12a9 9 0 1 0 3-6.7L3 8M3 3v5h5M12 7v5l3 2',
    store: 'M4 9l1.5-5h13L20 9M4 9h16v2a3 3 0 0 1-5.3 2 3 3 0 0 1-5.4 0A3 3 0 0 1 4 11zM5 13v7h14v-7M10 20v-4h4v4',
    warehouse: 'M3 9l9-5 9 5v11H3zM7 20v-8h10v8M7 15h10',
    factory: 'M3 20V10l5 3V10l5 3V6h4l1 14zM3 20h18',
    rotate: 'M20 12a8 8 0 1 1-2.3-5.7M20 4v5h-5',
    rotateL: 'M4 12a8 8 0 1 0 2.3-5.7M4 4v5h5',
    printer: 'M7 9V3h10v6M7 17H4v-7h16v7h-3M7 14h10v7H7z',
    download: 'M12 4v11M7 10l5 5 5-5M5 20h14',
    file: 'M6 3h8l5 5v13H6zM14 3v5h5M9 13h6M9 17h6',
    weight: 'M6 8h12l2 12H4zM12 8a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z',
    cube: 'M12 3l8 4.5v9L12 21l-8-4.5v-9zM12 12l8-4.5M12 12L4 7.5M12 12v9',
    bell: 'M6 16V11a6 6 0 0 1 12 0v5l2 2H4zM10 20a2 2 0 0 0 4 0',
    filter: 'M4 5h16l-6 8v6l-4-2v-4z',
    login: 'M10 4H5v16h5M14 8l4 4-4 4M18 12H9',
    exit: 'M14 4h5v16h-5M10 8l-4 4 4 4M6 12h9',
    pallet: 'M3 16h18M3 20h18M5 16v4M12 16v4M19 16v4M5 6h14v10H5zM5 11h14',
    layers: 'M12 3l9 5-9 5-9-5zM3 13l9 5 9-5M3 17.5l9 5 9-5',
    cart: 'M3 4h2l2.5 11h11L21 7H6.5M9 20a1 1 0 1 0 0-.01M18 20a1 1 0 1 0 0-.01',
    minus: 'M5 12h14',
    send: 'M4 12l16-8-6 16-3-6.5z',
    grid: 'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z',
    users: 'M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM2 21a7 7 0 0 1 14 0M16 3.5a4 4 0 0 1 0 7.5M18 14a7 7 0 0 1 4 7',
    split: 'M12 3v18M5 8l-2 4 2 4M19 8l2 4-2 4',
    info: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 11v6M12 7.5v.01',
    signal: 'M3 20h2v-3H3zM8 20h2v-7H8zM13 20h2v-11h-2zM18 20h2V5h-2z',
    battery: 'M3 8h15v8H3zM20 11v2'
  };
  function ic(name, size, sw) {
    size = size || 20;
    return '<svg width="' + size + '" height="' + size + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="' + (sw || 1.8) + '" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="' + (P[name] || P.box) + '"/></svg>';
  }
  /* Ilustraciones isométricas (Drakaniia/isometric) subidas como recursos */
  var A = {
    bulto: '/_blob/22703e1a591f4d8613c14c97e2fab84d', hojas: '/_blob/bb5b5c1dab8bf934ec20d84573c4ea05',
    lapices: '/_blob/e834e115ade1dd4cb88bf71dafbd0f37', clips: '/_blob/e79bb8a39aa82cb2ff3266fd81c4f26b',
    login: '/_blob/a0906de3930972255eb17195a3e9f836', cedis: '/_blob/75e6c57a6febfeeef315832cf1127da2',
    sucursal: '/_blob/b911d12139262f070fd6e7f4bfc1e5a7', anden: '/_blob/7502df155cf627f909f784ee6875b86f',
    embarque: '/_blob/983f425ecb85aa7b2fad7399e54c0e60', caseta: '/_blob/efe80427e454dde90c4f9f961ec5b02d',
    agenda: '/_blob/8a45d5130fcd36a899246903a1d9a0bb', impresora: '/_blob/52fc1113cfa0c4c0f9663a85ca87f205',
    datos: '/_blob/97e3404bc434918b7e33a3d3822cf58d', recibo: '/_blob/bf5e635937aa2b3cc29207bb07a729ba'
  };
  /* Catálogo: un SKU por bulto (no se mezclan productos) */
  var productos = [
    { sku: 'RES-0500', nombre: 'Resma carta 500 hojas', img: 'hojas', unidad: 'resmas', porBulto: 10, kg: 25.0, m3: 0.032 },
    { sku: 'CUA-0100', nombre: 'Cuaderno profesional 100 h', img: 'bulto', unidad: 'cuadernos', porBulto: 24, kg: 16.8, m3: 0.030 },
    { sku: 'FOL-0100', nombre: 'Folder carta crema', img: 'bulto', unidad: 'folders', porBulto: 100, kg: 9.6, m3: 0.024 },
    { sku: 'ENG-0020', nombre: 'Engrapadora metálica', img: 'bulto', unidad: 'piezas', porBulto: 20, kg: 8.2, m3: 0.020 },
    { sku: 'PAP-0100', nombre: 'Hojas carta, paquete 100', img: 'hojas', unidad: 'paquetes', porBulto: 10, kg: 5.1, m3: 0.018 },
    { sku: 'LAP-0012', nombre: 'Lápiz HB, caja 12', img: 'lapices', unidad: 'cajas', porBulto: 24, kg: 2.4, m3: 0.008 },
    { sku: 'CLI-0100', nombre: 'Clip #1, caja 100', img: 'clips', unidad: 'cajas', porBulto: 40, kg: 1.0, m3: 0.004 }
  ];
  function bySku(s) { for (var i = 0; i < productos.length; i++) if (productos[i].sku === s) return productos[i]; }
  /* Regla de colores por peso del bulto */
  function zona(kg) { return kg >= 15 ? 'roja' : kg >= 7 ? 'naranja' : 'verde'; }
  var zonas = {
    roja: { nombre: 'Caja roja', desc: 'Pesado · ≥ 15 kg', color: 'var(--pallet-heavy)', hex: '#d13438', fg: '#fff' },
    naranja: { nombre: 'Caja naranja', desc: 'Intermedio · 7–15 kg', color: 'var(--pallet-mid)', hex: '#f59e0b', fg: '#3a2300' },
    verde: { nombre: 'Caja verde', desc: 'Ligero · < 7 kg', color: 'var(--pallet-light)', hex: '#16884a', fg: '#fff' }
  };
  var sucursales = ['Suc. 01 Centro', 'Suc. 04 Xalapa', 'Suc. 07 Boca del Río', 'Suc. 12 Córdoba', 'Suc. 18 Orizaba', 'Suc. 21 Tuxpan'];
  var proveedores = ['Papelera del Golfo', 'Distribuidora Atlas', 'Grupo Escolar MX', 'Útiles del Sureste'];
  /* QR de ejemplo, determinista por texto */
  function qr(text, px) {
    px = px || 96; var n = 25, h = 0, i, s = '';
    for (i = 0; i < text.length; i++) h = (h * 31 + text.charCodeAt(i)) >>> 0;
    function rnd() { h ^= h << 13; h >>>= 0; h ^= h >> 17; h ^= h << 5; h >>>= 0; return h / 4294967296; }
    function finder(x, y) { return '<rect x="' + x + '" y="' + y + '" width="7" height="7"/><rect x="' + (x + 1) + '" y="' + (y + 1) + '" width="5" height="5" fill="#fff"/><rect x="' + (x + 2) + '" y="' + (y + 2) + '" width="3" height="3"/>'; }
    for (var y = 0; y < n; y++) for (var x = 0; x < n; x++) {
      var inF = (x < 8 && y < 8) || (x > n - 9 && y < 8) || (x < 8 && y > n - 9);
      if (!inF && rnd() > 0.52) s += '<rect x="' + x + '" y="' + y + '" width="1" height="1"/>';
    }
    return '<svg class="qr" width="' + px + '" height="' + px + '" viewBox="-1 -1 ' + (n + 2) + ' ' + (n + 2) + '" shape-rendering="crispEdges" role="img" aria-label="Código QR ' + text + '"><rect x="-1" y="-1" width="' + (n + 2) + '" height="' + (n + 2) + '" fill="#fff"/><g fill="#0f1f3d">' + s + finder(0, 0) + finder(n - 7, 0) + finder(0, n - 7) + '</g></svg>';
  }
  function statusBar() {
    return '<div class="sbar"><span>9:41</span><span class="dots">' + ic('signal', 14, 2) + ic('battery', 16, 2) + '</span></div>';
  }
  function toast(root, msg, icon) {
    var t = root.querySelector('.toast');
    if (!t) { t = document.createElement('div'); t.className = 'toast'; root.appendChild(t); }
    t.innerHTML = (icon ? ic(icon, 16, 2.2) : '') + '<span>' + msg + '</span>';
    t.classList.add('show'); clearTimeout(t._h); t._h = setTimeout(function () { t.classList.remove('show'); }, 1900);
  }
  function kg(n) { return (Math.round(n * 10) / 10).toLocaleString('es-MX') + ' kg'; }
  window.Cedis = { ic: ic, A: A, productos: productos, bySku: bySku, zona: zona, zonas: zonas, sucursales: sucursales, proveedores: proveedores, qr: qr, statusBar: statusBar, toast: toast, kg: kg };
})();
