from flask import Blueprint, g, redirect, render_template, request, url_for

from app.dados.base import db
from app.dados.modelos import ApoioManifesto

apoios_bp = Blueprint("apoios", __name__, url_prefix="/apoios")


def _exigir_login(proximo: str):
	if getattr(g, "usuario_email", None):
		return None

	return redirect(url_for("autenticacao.entrar", proximo=proximo))


@apoios_bp.get("/assinar")
def assinar_manifesto():
	redirecionamento = _exigir_login("/apoios/assinar")
	if redirecionamento:
		return redirecionamento

	apoio_existente = ApoioManifesto.query.filter_by(email=str(g.usuario_email).lower()).first()
	if apoio_existente:
		sucesso = "Sua assinatura já foi registrada. Obrigada pelo apoio!"
		return render_template("apoios/assinar.html", erro=None, sucesso=sucesso, nome=apoio_existente.nome)

	return render_template("apoios/assinar.html", erro=None, sucesso=None, nome="")


@apoios_bp.post("/assinar")
def salvar_assinatura_manifesto():
	redirecionamento = _exigir_login("/apoios/assinar")
	if redirecionamento:
		return redirecionamento

	nome = request.form.get("nome", "").strip()

	email = str(g.usuario_email).strip().lower()
	apoio_existente = ApoioManifesto.query.filter_by(email=email).first()
	if apoio_existente:
		sucesso = "Sua assinatura já foi registrada. Obrigada pelo apoio!"
		return render_template("apoios/assinar.html", erro=None, sucesso=sucesso, nome=apoio_existente.nome)

	db.session.add(ApoioManifesto(email=email, nome=nome))
	db.session.commit()

	sucesso = "Assinatura registrada com sucesso. Obrigada por apoiar o manifesto!"
	return render_template("apoios/assinar.html", erro=None, sucesso=sucesso, nome=nome)
