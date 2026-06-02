"""Entrega de resultados por email con plantillas HTML profesionales."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from modulo_1_servicio.scraping.models import ScrapeResult

logger = logging.getLogger(__name__)

HERE = Path(__file__).parent.parent
TEMPLATE_DIR = str(HERE / "templates")

_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


class EmailDelivery:
    """Entrega de resultados por correo electrónico.

    Configuración vía atributos de clase o variables de entorno.
    """

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = "scrapper@generico.dev"
    use_sendgrid: bool = False
    sendgrid_api_key: str = ""

    def send_results(
        self,
        result: ScrapeResult,
        result_id: str,
        recipients: tuple[str, ...],
        results_url: str = "",
    ) -> list[str]:
        """Envía resultados por email a los destinatarios.

        Returns:
            Lista de errores (vacía si todos fueron exitosos).
        """
        if not recipients:
            return ["No hay destinatarios configurados"]

        html = self._build_html(result, result_id, results_url)
        subject = f"📊 Resultados de scraping: {result.config.source}"

        errors: list[str] = []
        for email in recipients:
            try:
                self._send_one(email, subject, html)
                logger.info("Email enviado a %s", email)
            except Exception as e:
                logger.exception("Error enviando email a %s", email)
                errors.append(f"{email}: {e}")

        return errors

    def send_activation(self, email: str, wa_link: str) -> None:
        """Envía email de activación de WhatsApp con link wa.me."""
        html = f"""<!DOCTYPE html>
<html><body style="font-family: sans-serif; max-width: 600px; margin: 40px auto;">
<h2>Activa tus notificaciones de WhatsApp</h2>
<p>Haz clic en el siguiente enlace desde tu teléfono:</p>
<p><a href="{wa_link}" style="display: inline-block; padding: 12px 24px;
background: #25D366; color: white; text-decoration: none; border-radius: 6px;">
Activar WhatsApp</a></p>
<p>O escanea este código QR en tu WhatsApp.</p>
</body></html>"""
        self._send_one(email, "Activa tus notificaciones de WhatsApp", html)

    def _build_html(
        self, result: ScrapeResult, result_id: str, results_url: str
    ) -> str:
        template = _env.get_template("email_result.html")
        items_sample = [
            {"rank": i + 1, "data": item.data}
            for i, item in enumerate(result.items[:10])
        ]
        return template.render(
            source=result.config.source,
            total=result.success_count,
            errors=result.errors,
            elapsed=result.elapsed,
            items=items_sample,
            results_url=results_url,
            total_items=len(result.items),
            has_more=len(result.items) > 10,
        )

    def _send_one(self, to_email: str, subject: str, html: str) -> None:
        if self.use_sendgrid:
            self._send_sendgrid(to_email, subject, html)
        else:
            self._send_smtp(to_email, subject, html)

    def _send_smtp(self, to_email: str, subject: str, html: str) -> None:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            if self.smtp_user:
                server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.from_email, [to_email], msg.as_string())

    def _send_sendgrid(self, to_email: str, subject: str, html: str) -> None:
        import sendgrid  # type: ignore[import-untyped]
        from sendgrid.helpers.mail import Mail  # type: ignore[import-untyped]

        sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)
        mail = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html,
        )
        sg.client.mail.send.post(request_body=mail.get())
