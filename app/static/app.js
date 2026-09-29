"use strict";

/* ------------------------------------------------------------ utilidades */
const $ = (sel) => document.querySelector(sel);
const cuerpo = $("#cuerpo");
const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const sesion = {
  token: sessionStorage.getItem("token"),
  usuario: sessionStorage.getItem("usuario"),
  aviso: null,
};

function guardarSesion(token, usuario) {
  sesion.token = token;
  sesion.usuario = usuario;
  if (token) {
    sessionStorage.setItem("token", token);
    sessionStorage.setItem("usuario", usuario);
  } else {
    sessionStorage.removeItem("token");
    sessionStorage.removeItem("usuario");
  }
}

function cerrarSesion(texto) {
  guardarSesion(null, null);
  sesion.aviso = texto ? { tipo: "error", texto } : null;
  ir("login");
}

const fmtNota = (n) => String(Number(Number(n).toFixed(2)));

function edadDesde(fecha) {
  const [a, m, d] = fecha.split("-").map(Number);
  const hoy = new Date();
  let edad = hoy.getFullYear() - a;
  if (hoy.getMonth() + 1 < m || (hoy.getMonth() + 1 === m && hoy.getDate() < d)) edad -= 1;
  return edad;
}

function textoError(datos, codigo) {
  if (datos && typeof datos.detail === "string") return datos.detail;
  if (datos && Array.isArray(datos.detail)) {
    return datos.detail.map((d) => {
      const campo = (d.loc || []).filter((x) => x !== "body").join(".");
      return (campo ? campo + ": " : "") + String(d.msg).replace(/^Value error, /, "");
    }).join("; ");
  }
  return "No se pudo completar la operación (código " + codigo + ").";
}

async function api(ruta, opciones = {}) {
  const cabeceras = { "Content-Type": "application/json" };
  if (sesion.token) cabeceras.Authorization = "Bearer " + sesion.token;
  let resp;
  try {
    resp = await fetch("/api" + ruta, { ...opciones, headers: cabeceras });
  } catch (e) {
    throw new Error("No se pudo conectar con el servidor. Verifica que esté en ejecución.");
  }
  let datos = null;
  if (resp.status !== 204) {
    try { datos = await resp.json(); } catch (e) { datos = null; }
  }
  if (resp.status === 401 && sesion.token) {
    cerrarSesion("Tu sesión expiró. Inicia sesión de nuevo.");
    throw new Error("sesion");
  }
  if (!resp.ok) throw new Error(textoError(datos, resp.status));
  return datos;
}

function cabecera(texto) {
  $("#ruta").innerHTML = "<span>" + esc(texto) + "</span>" +
    (sesion.token ? '<button class="salir" id="salir" type="button">Salir</button>' : "");
  if (sesion.token) $("#salir").onclick = () => cerrarSesion();
}

function avisoHtml() {
  const a = sesion.aviso;
  sesion.aviso = null;
  return a ? '<p class="msg ' + a.tipo + '" role="status">' + esc(a.texto) + "</p>" : "";
}

function mostrarMsg(texto, tipo = "error") {
  const m = $("#msg");
  m.className = "msg " + tipo;
  m.textContent = texto;
  m.hidden = false;
  const f = $("#form");
  if (f && tipo === "error") {
    const ocultar = () => { m.hidden = true; };
    f.addEventListener("input", ocultar, { once: true });
    f.addEventListener("change", ocultar, { once: true });
  }
}

const campo = (id, etiqueta, tipo, extra = "", clase = "") =>
  '<div class="campo ' + clase + '"><label for="' + id + '">' + etiqueta + "</label>" +
  '<input id="' + id + '" name="' + id + '" type="' + tipo + '" ' + extra + "></div>";

const selector = (id, etiqueta, opciones, clase = "") =>
  '<div class="campo ' + clase + '"><label for="' + id + '">' + etiqueta + "</label>" +
  '<select id="' + id + '" name="' + id + '"><option value="" disabled selected>Seleccione una opción</option>' +
  opciones.map(([v, t]) => '<option value="' + esc(v) + '">' + esc(t) + "</option>").join("") +
  "</select></div>";

const MENU = [["inicio", "Inicio"], ["alumnos", "Alumnos"], ["programas", "Programas"],
              ["materias", "Materias"], ["profesores", "Profesores"], ["notas", "Notas"]];

function conMenu(activa, html) {
  return '<div class="layout"><nav class="lateral" aria-label="Menú principal">' +
    MENU.map(([k, t]) => '<button type="button" class="item' + (k === activa ? " activo" : "") +
      '" data-ir="' + k + '"' + (k === activa ? ' aria-current="page"' : "") + ">" + t + "</button>").join("") +
    '</nav><main class="contenido">' + html + "</main></div>";
}

function enlazar() {
  cuerpo.querySelectorAll("[data-ir]").forEach((b) => { b.onclick = () => ir(b.dataset.ir); });
}

function tablaNotas(notas, corta) {
  if (!notas.length) {
    return '<p class="vacio">Aún no hay notas registradas. Entra a Notas y usa «Registrar calificación» para agregar la primera.</p>';
  }
  const est = (e) => corta ? '<abbr title="' + e + '">' + (e === "Aprobado" ? "A" : "R") + "</abbr>" : e;
  const cab = corta
    ? "<th>Alumno</th><th>Materia</th><th>Final</th><th>Estado</th>"
    : "<th>Alumno</th><th>Materia</th><th>Profesor</th><th>Parcial 1</th><th>Parcial 2</th><th>Parcial 3</th><th>Final</th><th>Estado</th>";
  const filas = notas.map((n) => corta
    ? "<tr><td>" + esc(n.alumno) + "</td><td>" + esc(n.materia) + "</td><td>" + fmtNota(n.nota_final) + "</td><td>" + est(n.estado) + "</td></tr>"
    : "<tr><td>" + esc(n.alumno) + "</td><td>" + esc(n.materia) + "</td><td>" + esc(n.profesor) + "</td><td>" + fmtNota(n.parcial1) +
      "</td><td>" + fmtNota(n.parcial2) + "</td><td>" + fmtNota(n.parcial3) + "</td><td>" + fmtNota(n.nota_final) + "</td><td>" + est(n.estado) + "</td></tr>").join("");
  return '<div class="tabla"><table><thead><tr>' + cab + "</tr></thead><tbody>" + filas + "</tbody></table></div>";
}

/* ------------------------------------------------- inicio de sesión / registro */
function vLogin(registro = false) {
  cabecera(registro ? "Crear cuenta" : "Iniciar sesión");
  cuerpo.innerHTML =
    '<div class="pagina estrecha"><h1>' + (registro ? "Crear cuenta" : "Iniciar sesión") + "</h1>" +
    '<p class="sub">' + (registro ? "Registra un usuario para administrar el sistema académico." : "Ingresa con tu correo y contraseña.") + "</p>" +
    avisoHtml() +
    '<form id="form" novalidate>' +
    (registro ? campo("nombre", "Nombre completo", "text", 'autocomplete="name"') : "") +
    campo("email", "Correo electrónico", "email", 'autocomplete="email"') +
    campo("password", "Contraseña", "password", 'autocomplete="' + (registro ? "new-password" : "current-password") + '"') +
    '<p class="msg error" id="msg" role="alert" hidden></p>' +
    '<div class="botones"><button type="submit" class="btn">' + (registro ? "Registrarme" : "Ingresar") + "</button>" +
    '<button type="button" class="btn claro" id="alterna">' + (registro ? "Ya tengo cuenta" : "Crear cuenta") + "</button></div></form></div>";

  $("#alterna").onclick = () => vLogin(!registro);
  $("#form").onsubmit = async (ev) => {
    ev.preventDefault();
    const email = $("#email").value.trim();
    const password = $("#password").value;
    try {
      if (!/^\S+@\S+\.\S+$/.test(email)) throw new Error("Escribe un correo válido, por ejemplo nombre@dominio.co.");
      if (registro) {
        const nombre = $("#nombre").value.trim();
        if (nombre.length < 3) throw new Error("El nombre debe tener al menos 3 caracteres.");
        if (password.length < 8 || !/[A-Za-z]/.test(password) || !/\d/.test(password)) {
          throw new Error("La contraseña debe tener al menos 8 caracteres, con letras y números.");
        }
        await api("/auth/registro", { method: "POST", body: JSON.stringify({ nombre, email, password }) });
      } else if (!password) {
        throw new Error("Escribe tu contraseña.");
      }
      const r = await api("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
      guardarSesion(r.access_token, r.usuario);
      ir("inicio");
    } catch (e) {
      if (e.message !== "sesion") mostrarMsg(e.message);
    }
  };
}

/* ------------------------------------------------------------------ inicio */
async function vInicio() {
  const [res, notas] = await Promise.all([api("/resumen"), api("/notas?limite=5")]);
  cabecera(sesion.usuario);
  cuerpo.innerHTML = conMenu("inicio",
    avisoHtml() + "<h1>Resumen académico</h1>" +
    '<div class="tarjetas">' +
    [["Alumnos", res.alumnos], ["Materias", res.materias], ["Aprobadas", res.aprobadas]]
      .map(([t, n]) => '<div class="tarjeta"><span>' + t + "</span><strong>" + n + "</strong></div>").join("") +
    "</div><h2>Notas recientes</h2>" + tablaNotas(notas, true));
  enlazar();
}

/* ----------------------------------------------------------------- alumnos */
async function vAlumnos() {
  const alumnos = await api("/alumnos");
  cabecera("Alumnos");
  const filas = alumnos.map((a) =>
    "<tr><td>" + a.codigo + "</td><td>" + esc(a.nombre_completo) + "</td><td>" + a.edad + "</td><td>" + esc(a.ciudad) +
    "</td><td>" + esc(a.programa_codigo) + '</td><td><button type="button" class="btn peligro" data-borrar="' + a.codigo +
    '" data-nombre="' + esc(a.nombre_completo) + '">Eliminar</button></td></tr>').join("");
  cuerpo.innerHTML = conMenu("alumnos",
    '<div class="barra-acciones"><h1>Alumnos</h1><button type="button" class="btn chico" data-ir="alumno-nuevo">Nuevo estudiante</button></div>' +
    avisoHtml() +
    (alumnos.length
      ? '<div class="tabla"><table><thead><tr><th>Código</th><th>Nombre completo</th><th>Edad</th><th>Ciudad</th><th>Programa</th><th></th></tr></thead><tbody>' + filas + "</tbody></table></div>"
      : '<p class="vacio">Aún no hay alumnos registrados. Usa «Nuevo estudiante» para agregar el primero.</p>'));
  enlazar();
  cuerpo.querySelectorAll("[data-borrar]").forEach((b) => {
    b.onclick = async () => {
      if (!confirm("¿Eliminar a " + b.dataset.nombre + "? También se borrarán sus notas.")) return;
      try {
        await api("/alumnos/" + b.dataset.borrar, { method: "DELETE" });
        sesion.aviso = { tipo: "ok", texto: "Alumno eliminado: " + b.dataset.nombre + "." };
        ir("alumnos");
      } catch (e) {
        if (e.message !== "sesion") { sesion.aviso = { tipo: "error", texto: e.message }; ir("alumnos"); }
      }
    };
  });
}

async function vAlumnoNuevo() {
  const programas = await api("/programas");
  cabecera("Alumnos / Nuevo estudiante");
  cuerpo.innerHTML =
    '<div class="pagina"><h1>Registrar nuevo estudiante</h1>' +
    '<p class="sub">Complete los datos del alumno y seleccione su programa académico.</p>' +
    '<form id="form" novalidate><div class="rejilla">' +
    campo("codigo", "Código", "number", 'min="1" step="1" inputmode="numeric"') +
    campo("nombre_completo", "Nombre completo", "text", 'maxlength="100" autocomplete="off"') +
    campo("edad", "Edad", "number", 'min="5" max="100" step="1" inputmode="numeric"') +
    campo("fecha_nacimiento", "Fecha de nacimiento", "date") +
    campo("ciudad", "Ciudad", "text", 'maxlength="60" autocomplete="off"') +
    selector("genero", "Género", [["Femenino", "Femenino"], ["Masculino", "Masculino"], ["Otro", "Otro"]]) +
    selector("programa_codigo", "Programa", programas.map((p) => [p.codigo, p.codigo + " - " + p.nombre]), "ancho") +
    '</div><p class="msg error" id="msg" role="alert" hidden></p>' +
    '<div class="botones"><button type="button" class="btn claro" id="cancelar">Cancelar</button>' +
    '<button type="submit" class="btn">Registrar alumno</button></div></form></div>';

  $("#cancelar").onclick = () => ir("alumnos");
  $("#fecha_nacimiento").onchange = (ev) => {
    if (ev.target.value) $("#edad").value = edadDesde(ev.target.value);
  };
  $("#form").onsubmit = async (ev) => {
    ev.preventDefault();
    const datos = {
      codigo: parseInt($("#codigo").value, 10),
      nombre_completo: $("#nombre_completo").value.trim(),
      edad: parseInt($("#edad").value, 10),
      fecha_nacimiento: $("#fecha_nacimiento").value,
      ciudad: $("#ciudad").value.trim(),
      genero: $("#genero").value,
      programa_codigo: $("#programa_codigo").value,
    };
    try {
      if (!(datos.codigo > 0)) throw new Error("Escribe un código numérico mayor que cero.");
      if (datos.nombre_completo.length < 3) throw new Error("El nombre completo debe tener al menos 3 caracteres.");
      if (!datos.fecha_nacimiento) throw new Error("Selecciona la fecha de nacimiento.");
      const real = edadDesde(datos.fecha_nacimiento);
      if (real < 0) throw new Error("La fecha de nacimiento no puede ser futura.");
      if (!(datos.edad >= 5 && datos.edad <= 100)) throw new Error("La edad debe estar entre 5 y 100 años.");
      if (datos.edad !== real) throw new Error("La edad no coincide con la fecha de nacimiento (debería ser " + real + ").");
      if (datos.ciudad.length < 2) throw new Error("Escribe la ciudad.");
      if (!datos.genero) throw new Error("Selecciona el género.");
      if (!datos.programa_codigo) throw new Error("Selecciona el programa académico.");
      await api("/alumnos", { method: "POST", body: JSON.stringify(datos) });
      sesion.aviso = { tipo: "ok", texto: "Alumno registrado: " + datos.codigo + " - " + datos.nombre_completo + "." };
      ir("alumnos");
    } catch (e) {
      if (e.message !== "sesion") mostrarMsg(e.message);
    }
  };
}

/* --------------------------------------------------- programas, materias, profesores */
const CATALOGOS = {
  programas: { titulo: "Programas", uno: "programa", numerico: false },
  materias: { titulo: "Materias", uno: "materia", numerico: true },
  profesores: { titulo: "Profesores", uno: "profesor", numerico: true },
};

async function vCatalogo(tipo) {
  const cfg = CATALOGOS[tipo];
  const lista = await api("/" + tipo);
  cabecera(cfg.titulo);
  cuerpo.innerHTML = conMenu(tipo,
    "<h1>" + cfg.titulo + "</h1>" + avisoHtml() +
    '<form id="form" class="inline" novalidate style="margin-top:18px">' +
    campo("codigo", "Código", cfg.numerico ? "number" : "text", cfg.numerico ? 'min="1" step="1"' : 'maxlength="10"') +
    campo("nombre", "Nombre", "text", 'maxlength="100" autocomplete="off"') +
    '<button type="submit" class="btn chico">Agregar ' + cfg.uno + "</button></form>" +
    '<p class="msg error" id="msg" role="alert" hidden style="margin:-8px 0 18px"></p>' +
    (lista.length
      ? '<div class="tabla"><table><thead><tr><th>Código</th><th>Nombre</th></tr></thead><tbody>' +
        lista.map((f) => "<tr><td>" + esc(f.codigo) + "</td><td>" + esc(f.nombre) + "</td></tr>").join("") + "</tbody></table></div>"
      : '<p class="vacio">Aún no hay registros en esta lista.</p>'));
  enlazar();
  $("#form").onsubmit = async (ev) => {
    ev.preventDefault();
    const nombre = $("#nombre").value.trim();
    const codigoTxt = $("#codigo").value.trim();
    try {
      if (!codigoTxt) throw new Error("Escribe el código.");
      if (cfg.numerico && !(parseInt(codigoTxt, 10) > 0)) throw new Error("El código debe ser un número mayor que cero.");
      if (nombre.length < 3) throw new Error("El nombre debe tener al menos 3 caracteres.");
      const codigo = cfg.numerico ? parseInt(codigoTxt, 10) : codigoTxt;
      await api("/" + tipo, { method: "POST", body: JSON.stringify({ codigo, nombre }) });
      sesion.aviso = { tipo: "ok", texto: "Registro agregado: " + codigoTxt + " - " + nombre + "." };
      ir(tipo);
    } catch (e) {
      if (e.message !== "sesion") mostrarMsg(e.message);
    }
  };
}

/* ------------------------------------------------------------------- notas */
async function vNotas() {
  const notas = await api("/notas?limite=100");
  cabecera("Notas");
  cuerpo.innerHTML = conMenu("notas",
    '<div class="barra-acciones"><h1>Notas</h1><button type="button" class="btn chico" data-ir="nota-nueva">Registrar calificación</button></div>' +
    avisoHtml() + tablaNotas(notas, false));
  enlazar();
}

async function vNotaNueva() {
  const [alumnos, materias, profesores] = await Promise.all([api("/alumnos"), api("/materias"), api("/profesores")]);
  cabecera("Notas / Registrar calificación");
  if (!alumnos.length) {
    cuerpo.innerHTML = '<div class="pagina"><h1>Registrar calificación</h1>' +
      '<p class="msg error">No hay alumnos registrados. Registra un alumno antes de calificar.</p>' +
      '<div class="botones"><button type="button" class="btn claro" id="cancelar">Volver</button>' +
      '<button type="button" class="btn" data-ir="alumno-nuevo">Nuevo estudiante</button></div></div>';
    $("#cancelar").onclick = () => ir("notas");
    enlazar();
    return;
  }
  const nota = (id, etiqueta) => campo(id, etiqueta, "number", 'min="0" max="5" step="0.1" inputmode="decimal"');
  cuerpo.innerHTML =
    '<div class="pagina"><h1>Registrar calificación</h1>' +
    '<p class="sub">Escriba las tres notas parciales (de 0.0 a 5.0). La nota final es el promedio.</p>' +
    '<form id="form" novalidate><div class="rejilla">' +
    selector("alumno_codigo", "Alumno", alumnos.map((a) => [a.codigo, a.codigo + " - " + a.nombre_completo])) +
    selector("materia_codigo", "Materia", materias.map((m) => [m.codigo, m.codigo + " - " + m.nombre])) +
    selector("profesor_codigo", "Profesor", profesores.map((p) => [p.codigo, p.codigo + " - " + p.nombre])) +
    nota("parcial1", "Parcial 1") + nota("parcial2", "Parcial 2") + nota("parcial3", "Parcial 3") +
    '</div><p class="resultado" id="resultado" aria-live="polite"></p>' +
    '<p class="msg error" id="msg" role="alert" hidden></p>' +
    '<div class="botones"><button type="submit" class="btn">Guardar y calcular</button>' +
    '<button type="button" class="btn claro" id="cancelar">Cancelar</button></div></form></div>';

  const leer = () => ["parcial1", "parcial2", "parcial3"].map((id) => parseFloat($("#" + id).value));
  const valida = (n) => !Number.isNaN(n) && n >= 0 && n <= 5;
  const previsualizar = () => {
    const p = leer();
    const r = $("#resultado");
    if (!p.every(valida)) { r.textContent = ""; r.className = "resultado"; return; }
    const final = Number(((p[0] + p[1] + p[2]) / 3).toFixed(2));
    const aprobado = final >= 3.0;
    r.className = "resultado" + (aprobado ? "" : " rep");
    r.textContent = "Resultado esperado: nota final " + fmtNota(final) + " | Estado " + (aprobado ? "Aprobado" : "Reprobado");
  };
  ["parcial1", "parcial2", "parcial3"].forEach((id) => { $("#" + id).oninput = previsualizar; });
  $("#cancelar").onclick = () => ir("notas");

  $("#form").onsubmit = async (ev) => {
    ev.preventDefault();
    const p = leer();
    try {
      if (!$("#alumno_codigo").value) throw new Error("Selecciona el alumno.");
      if (!$("#materia_codigo").value) throw new Error("Selecciona la materia.");
      if (!$("#profesor_codigo").value) throw new Error("Selecciona el profesor.");
      if (!p.every(valida)) throw new Error("Cada parcial debe ser un número entre 0.0 y 5.0.");
      const r = await api("/notas", { method: "POST", body: JSON.stringify({
        alumno_codigo: parseInt($("#alumno_codigo").value, 10),
        materia_codigo: parseInt($("#materia_codigo").value, 10),
        profesor_codigo: parseInt($("#profesor_codigo").value, 10),
        parcial1: p[0], parcial2: p[1], parcial3: p[2],
      }) });
      ["parcial1", "parcial2", "parcial3"].forEach((id) => { $("#" + id).value = ""; });
      $("#resultado").textContent = "";
      mostrarMsg("Nota guardada. Nota final " + fmtNota(r.nota_final) + " | Estado " + r.estado, "ok");
    } catch (e) {
      if (e.message !== "sesion") mostrarMsg(e.message);
    }
  };
}

/* ------------------------------------------------------------- navegación */
const VISTAS = {
  login: () => vLogin(false),
  inicio: vInicio,
  alumnos: vAlumnos,
  "alumno-nuevo": vAlumnoNuevo,
  programas: () => vCatalogo("programas"),
  materias: () => vCatalogo("materias"),
  profesores: () => vCatalogo("profesores"),
  notas: vNotas,
  "nota-nueva": vNotaNueva,
};

async function ir(vista) {
  if (!sesion.token && vista !== "login") vista = "login";
  try {
    await VISTAS[vista]();
  } catch (e) {
    if (e.message === "sesion") return;
    cabecera("Error");
    cuerpo.innerHTML = '<div class="pagina"><h1>No se pudo cargar la pantalla</h1><p class="msg error">' + esc(e.message) +
      '</p><div class="botones"><button type="button" class="btn" id="reintentar">Reintentar</button></div></div>';
    $("#reintentar").onclick = () => ir(vista);
  }
}

ir(sesion.token ? "inicio" : "login");
