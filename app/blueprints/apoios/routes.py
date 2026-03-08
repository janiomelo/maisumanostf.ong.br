from flask import Blueprint, current_app, g, redirect, render_template, request, url_for
from sqlalchemy import func

from app.comunicacao import ErroClienteResend, enviar_email_confirmacao_apoio
from app.dados.base import db
from app.dados.modelos import ApoioManifesto
from app.dados.protocolo import abreviar_protocolo

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

	apoio = ApoioManifesto(email=email, nome=nome)
	db.session.add(apoio)
	db.session.commit()
	total_apoios_ativos = db.session.query(func.count(ApoioManifesto.id)).scalar() or 0
	_despachar_email_confirmacao(
		email=email,
		nome=nome,
		protocolo_publico=abreviar_protocolo(apoio.protocolo),
		total_apoios_ativos=int(total_apoios_ativos),
	)

	sucesso = "Assinatura registrada com sucesso. Obrigada por apoiar o manifesto!"
	return _render_assinar(erro=None, sucesso=sucesso, nome=nome, apoio_registrado=True)


def _despachar_email_confirmacao(*, email: str, nome: str, protocolo_publico: str, total_apoios_ativos: int) -> None:
	try:
		enviar_email_confirmacao_apoio(
			config=current_app.config,
			destinatario=email,
			nome_publico=nome,
			protocolo_publico=protocolo_publico,
			total_apoios_ativos=total_apoios_ativos,
			url_site=request.url_root,
		)
	except (ErroClienteResend, RuntimeError, ValueError) as exc:
		# O apoio fica registrado mesmo se o envio do e-mail falhar.
		current_app.logger.warning("Falha ao enviar e-mail de confirmacao de apoio para %s: %s", email, exc)


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
