from collections import defaultdict
from pathlib import Path
import base64
from markupsafe import Markup

from odoo import api, fields, models, tools, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    amount_total_words = fields.Char(string="Amount total in words", compute="_compute_amount_total_words", )
    pi_qty_override = fields.Float(string="PI Qty Override")
    pi_summary_override = fields.Text(
        string="PI Summary Override",
        help="Manually entered description to show on the Proforma Invoice "
             "product line. If empty, an automatic summary is generated.",
    )

    # Stores the final "prize" (amount) chosen in the wizard — whether it's
    # the full order amount or a partial payment (25% / 50% / 75% / custom).
    # This is what actually gets printed on the report.
    pi_amount_override = fields.Float(
        string="PI Amount Override",
        help="Amount to show on the Proforma Invoice (set from the PI "
             "Summary wizard). If 0.0, the full order amount is used.",
    )
    parent_sale_order_id = fields.Many2one(
        "sale.order",
        string="Parent Sale Order",
        copy=False,
        index=True,
        ondelete="restrict",
        help="If set, this order was created as additional/related work "
             "against the referenced Sale Order.",
    )
    child_sale_order_ids = fields.One2many(
        "sale.order",
        "parent_sale_order_id",
        string="Related Sale Orders",
    )
    child_sale_order_count = fields.Integer(
        string="Related Orders Count",
        compute="_compute_child_sale_order_count",
    )
    subject = fields.Char(string="Subject")
    job_reference = fields.Char(string="Job Reference")
    reference = fields.Char(string=" Reference")
    lpo_ref = fields.Char(string='LPO')
    attention = fields.Char(string='Attention')
    pi_history_ids = fields.One2many(
        "sale.order.pi.history",
        "sale_order_id",
        string="Proforma Invoices",
    )
    pi_history_count = fields.Integer(
        string="Proforma Invoice Count",
        compute="_compute_pi_history_count",
    )

    @api.depends("pi_history_ids")
    def _compute_pi_history_count(self):
        for order in self:
            order.pi_history_count = len(order.pi_history_ids)

    def _get_next_pi_name(self):
        self.ensure_one()
        existing = self.env["sale.order.pi.history"].search_count(
            [("sale_order_id", "=", self.id)]
        )
        return "%s -- PI -%02d" % (self.name, existing + 1)

    def action_view_pi_history(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Proforma Invoices"),
            "res_model": "sale.order.pi.history",
            "view_mode": "list,form",
            "domain": [("sale_order_id", "=", self.id)],
            "context": {"default_sale_order_id": self.id},
        }

    @api.depends('amount_total', 'currency_id')
    def _compute_amount_total_words(self):
        for rec in self:
            rec.amount_total_words = rec.currency_id.amount_to_text(rec.amount_total).replace(',', '')

    @api.depends("child_sale_order_ids")
    def _compute_child_sale_order_count(self):
        for order in self:
            order.child_sale_order_count = len(order.child_sale_order_ids)

    def _get_root_sale_order(self):
        """Walk up the parent chain so numbering is always relative to the
        original order, even if a child order is used to spawn another
        related order."""
        self.ensure_one()
        root = self
        while root.parent_sale_order_id:
            root = root.parent_sale_order_id
        return root

    def _get_next_child_name(self, root):
        siblings = self.env["sale.order"].search(
            [("parent_sale_order_id", "=", root.id)]
        )
        indexes = []
        for sibling in siblings:
            suffix = sibling.name.split("/")[-1]
            if suffix.isdigit():
                indexes.append(int(suffix))
        next_index = max(indexes, default=0) + 1
        return "%s/%02d" % (root.name, next_index)

    def action_create_child_sale_order(self):
        self.ensure_one()
        root = self._get_root_sale_order()
        new_name = self._get_next_child_name(root)

        new_order = root.copy(
            default={
                "name": new_name,
                "parent_sale_order_id": root.id,
                "partner_id": root.partner_id.id,
                "order_line": [],
                "origin": root.name,
            }
        )

        new_order.message_post(
            body=Markup(_("Related order created from %s.")) % root._get_html_link()
        )
        root.message_post(
            body=Markup(_("Related order %s created.")) % new_order._get_html_link()
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Related Sale Order"),
            "res_model": "sale.order",
            "view_mode": "form",
            "res_id": new_order.id,
            "target": "current",
        }

    def action_view_child_sale_orders(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Related Sale Orders"),
            "res_model": "sale.order",
            "view_mode": "list,form",
            "domain": [("parent_sale_order_id", "=", self.id)],
            "context": {"default_parent_sale_order_id": self.id},
        }

    def _get_wwd_header_image_uri(self):
        try:
            path = tools.file_path(
                "wood_world_customistation/static/src/img/wood_world_header.png"
            )
        except FileNotFoundError:
            return ""
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return "data:image/png;base64,%s" % data

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

    def get_printed_datetime(self):
        self.ensure_one()
        return fields.Datetime.context_timestamp(
            self,
            fields.Datetime.now()
        ).strftime("%d/%m/%Y %I:%M:%S %p")

    def _get_auto_summary_description(self):
        """The original automatic aggregation logic, kept separate so the
        wizard can use it as a default value too."""
        self.ensure_one()

        lines = self.order_line.filtered(
            lambda l: not l.display_type and not l.is_downpayment
        )

        products = defaultdict(float)
        for line in lines:
            products[line.product_id.display_name or line.name] += line.price_subtotal

        main_items = sorted(products.items(), key=lambda item: item[1], reverse=True)
        names = [name for name, _ in main_items]

        return ", ".join(names[:3]) + (" & Others" if len(names) > 3 else "")

    def _get_simplified_report_summary(self):
        self.ensure_one()

        lines = self.order_line.filtered(
            lambda l: not l.display_type and not l.is_downpayment
        )

        description = self.pi_summary_override or self._get_auto_summary_description()

        if self.pi_amount_override:
            # Wizard set a specific "prize" (full or partial payment) —
            # use it directly for both the line amount and the printed
            # net total, since a partial-payment PI doesn't need its own
            # tax breakdown.
            amount = self.pi_amount_override
            total = self.pi_amount_override
        else:
            amount = sum(lines.mapped("price_subtotal"))
            total = sum(lines.mapped("price_total"))

        return {
            "description": description,
            "amount": amount,
            "total": total,
        }

    def action_open_pi_summary_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Proforma Invoice Summary",
            "res_model": "sale.order.pi.summary.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_sale_order_id": self.id,
            },
        }
