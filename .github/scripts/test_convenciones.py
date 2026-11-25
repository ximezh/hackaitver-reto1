import unittest

from convenciones import dueno, revisar


def pr(
    rama="front-feat/sprint1",
    titulo="feat(front): login web (sprint 1)",
    base="dev",
    archivos=("front/src/views/LoginWeb.vue",),
    asuntos=("feat(front): agrega el login web",),
    etiquetas=(),
):
    return revisar(base, rama, titulo, set(etiquetas), list(archivos), list(asuntos))


class Dueno(unittest.TestCase):
    def test_rutas_por_area(self):
        self.assertEqual(dueno("front/src/views/Caseta.vue"), "front")
        self.assertEqual(dueno("front/src/api/http.js"), "devops")
        self.assertEqual(dueno("front/vite.config.js"), "devops")
        self.assertEqual(dueno("back/app/main.py"), "back")
        self.assertEqual(dueno("back/Dockerfile"), "devops")
        self.assertEqual(dueno("back/.dockerignore"), "devops")
        self.assertEqual(dueno("front/nginx.conf.template"), "devops")
        self.assertEqual(dueno("compose.yaml"), "back")
        self.assertEqual(dueno("docs/api/sprint-1.md"), "back")
        self.assertEqual(dueno("docs/scrum/front.md"), "front")
        self.assertEqual(dueno(".github/workflows/ci.yml"), "devops")
        self.assertEqual(dueno("design/CEDIS Flow/tokens.css"), "diseno")
        self.assertEqual(dueno("docs/scrum.md"), "compartido")
        self.assertIsNone(dueno("otra/cosa.txt"))

    def test_no_confunde_prefijos(self):
        self.assertIsNone(dueno("frontend/x.js"))
        self.assertIsNone(dueno("CLAUDE.md.bak"))


class Revisar(unittest.TestCase):
    def test_pr_correcto(self):
        res = pr()
        self.assertEqual(res.errores, [])
        self.assertEqual(res.avisos, [])

    def test_rama_invalida(self):
        res = pr(rama="feat/login")
        self.assertIn("no sigue `<área>-<tipo>/sprint<N>`", res.errores[0])

    def test_titulo_sin_alcance_del_area(self):
        res = pr(titulo="feat: login web")
        self.assertTrue(any("alcance del área" in e for e in res.errores))

    def test_titulo_no_convencional(self):
        res = pr(titulo="Login web")
        self.assertTrue(any("Conventional Commits" in e for e in res.errores))

    def test_commit_de_otra_area(self):
        res = pr(asuntos=("feat(back): agrega login",))
        self.assertTrue(any("el alcance debe ser `front`" in e for e in res.errores))

    def test_commit_scrum_permitido(self):
        res = pr(asuntos=("docs(scrum): cierra el sprint 1 de front",))
        self.assertEqual(res.errores, [])

    def test_archivo_de_otra_area(self):
        res = pr(archivos=("back/app/main.py",))
        self.assertTrue(any("es de `back`" in e for e in res.errores))

    def test_front_no_edita_api(self):
        res = pr(archivos=("front/src/api/http.js",))
        self.assertTrue(any("es de `devops`" in e for e in res.errores))

    def test_design_bloqueado_sin_etiqueta(self):
        res = pr(archivos=("design/CEDIS Flow/tokens.css",))
        self.assertTrue(any("solo lectura" in e for e in res.errores))

    def test_design_con_etiqueta(self):
        res = pr(archivos=("design/CEDIS Flow/tokens.css",), etiquetas=("diseno-autorizado",))
        self.assertEqual(res.errores, [])

    def test_compartido_es_aviso(self):
        res = pr(archivos=("README.md",))
        self.assertEqual(res.errores, [])
        self.assertEqual(len(res.avisos), 1)

    def test_ruta_sin_dueno(self):
        res = pr(archivos=("otra/cosa.txt",))
        self.assertTrue(any("no tiene dueño" in e for e in res.errores))

    def test_excepcion_axios_sprint0(self):
        res = pr(
            rama="devops-chore/sprint0",
            titulo="chore(devops): axios",
            archivos=("front/package.json",),
            asuntos=("chore(devops): agrega axios",),
        )
        self.assertEqual(res.errores, [])
        self.assertEqual(len(res.avisos), 1)

    def test_excepcion_axios_solo_sprint0(self):
        res = pr(
            rama="devops-chore/sprint1",
            titulo="chore(devops): axios",
            archivos=("front/package.json",),
            asuntos=("chore(devops): agrega axios",),
        )
        self.assertTrue(any("es de `front`" in e for e in res.errores))

    def test_dev_a_main(self):
        res = pr(
            base="main",
            rama="dev",
            titulo="feat: cierre del sprint 1",
            archivos=("back/app/main.py", "front/src/App.vue"),
            asuntos=("cualquier cosa",),
        )
        self.assertEqual(res.errores, [])

    def test_main_solo_desde_dev(self):
        res = pr(base="main", rama="front-feat/sprint1")
        self.assertTrue(any("solo recibe PR desde `dev`" in e for e in res.errores))


if __name__ == "__main__":
    unittest.main()
