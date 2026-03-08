from flask import Blueprint, g, redirect, render_template, request, url_for

from app.dados.base import db
from app.dados.modelos import ApoioManifesto

apoios_bp = Blueprint("apoios", __name__, url_prefix="/apoios")


def _exigir_login(proximo: str):
	if getattr(g, "usuario_email", None):
		return None

	return redirect(url_for("autenticacao.entrar", proximo=proximo))


def _render_assinar(erro: str | None, sucesso: str | None, nome: str, apoio_registrado: bool):
	return render_template(
		"apoios/assinar.html",
		erro=erro,
		sucesso=sucesso,
		nome=nome,
		apoio_registrado=apoio_registrado,
	)


@apoios_bp.get("/assinar")
def assinar_manifesto():
	redirecionamento = _exigir_login("/apoios/assinar")
	if redirecionamento:
		return redirecionamento

	apoio_existente = ApoioManifesto.query.filter_by(email=str(g.usuario_email).lower()).first()
	if apoio_existente:
		sucesso = "Sua assinatura já foi registrada. Obrigada pelo apoio!"
		return _render_assinar(erro=None, sucesso=sucesso, nome=apoio_existente.nome, apoio_registrado=True)

	return _render_assinar(erro=None, sucesso=None, nome="", apoio_registrado=False)


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
		return _render_assinar(erro=None, sucesso=sucesso, nome=apoio_existente.nome, apoio_registrado=True)

	db.session.add(ApoioManifesto(email=email, nome=nome))
	db.session.commit()

	sucesso = "Assinatura registrada com sucesso. Obrigada por apoiar o manifesto!"
	return _render_assinar(erro=None, sucesso=sucesso, nome=nome, apoio_registrado=True)


@apoios_bp.post("/remover")
def remover_assinatura_manifesto():
	redirecionamento = _exigir_login("/apoios/assinar")
	if redirecionamento:
		return redirecionamento

	email = str(g.usuario_email).strip().lower()
	apoio_existente = ApoioManifesto.query.filter_by(email=email).first()
	if not apoio_existente:
		sucesso = "Nenhum apoio ativo foi encontrado para remoção."
		return _render_assinar(erro=None, sucesso=sucesso, nome="", apoio_registrado=False)

	db.session.delete(apoio_existente)
	db.session.commit()

	sucesso = "Seu apoio foi removido com sucesso."
	return _render_assinar(erro=None, sucesso=sucesso, nome="", apoio_registrado=False)
