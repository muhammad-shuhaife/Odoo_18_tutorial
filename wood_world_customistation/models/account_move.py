import base64
from pathlib import Path
from odoo import fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    project_id = fields.Many2one(
        comodel_name="project.project",
        string="Project",
    )
    subject = fields.Char(string="Subject")
    job_reference = fields.Char(string="Job Reference")
    reference = fields.Char(string=" Reference")
    lpo_ref = fields.Char(string='LPO')
    attention = fields.Char(string='Attention')
    def _get_logo_base64(self):
        logo_path = (
                Path(__file__).resolve().parent.parent
                / "static"
                / "src"
                / "img"
                / "logo.jpg"
        )

        return (
            base64.b64encode(logo_path.read_bytes()).decode("utf-8")
            if logo_path.exists()
            else False
        )
