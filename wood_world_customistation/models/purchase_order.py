import base64
from pathlib import Path
from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    remarks = fields.Text(string="Remarks")
    delivery_term_id = fields.Char(string="Delivery Term")
    delivery_details = fields.Char(string="Delivery Details")
    subject = fields.Char(string="Subject")
    job_reference = fields.Char(string="Job Reference")
    reference = fields.Char(string=" Reference")

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


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_job_reference = fields.Many2one(
        comodel_name='project.project',
        string='Job Reference',
        help="Reference to the project/job this purchase order line relates to.",
    )

    def get_report_description(self):
        """Returns a clean description for PDF reports: unescaped name
        with the project/job reference appended in brackets, if set."""
        self.ensure_one()
        name = unescape(self.name or '')
        if self.project_job_ref:
            name = '%s (%s)' % (name, self.product_job_reference.name)
        return name
