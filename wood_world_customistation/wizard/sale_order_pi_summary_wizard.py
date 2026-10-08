from odoo import api, fields, models


class SaleOrderPiSummaryWizard(models.TransientModel):
    _name = "sale.order.pi.summary.wizard"
    _description = "Proforma Invoice Summary Wizard"

    sale_order_id = fields.Many2one(
        "sale.order",
        string="Sale Order",
        required=True,
    )

    order_line_ids = fields.One2many(
        related="sale_order_id.order_line",
        string="Order Lines",
        readonly=True,
    )

    summary = fields.Text(
        string="Summary",
        required=True,
    )

    full_amount = fields.Float(
        string="Full Order Amount",
        readonly=True,
    )

    payment_percentage = fields.Selection(
        [
            ("25", "25%"),
            ("50", "50%"),
            ("75", "75%"),
            ("custom", "Custom"),
        ],
        string="Payment %",
        default="custom",
        required=True,
    )

    amount = fields.Float(
        string="Amount",
        required=True,
    )

    qty = fields.Float(
        string="Qty",
        required=True,
        help="Total quantity to print on the Proforma Invoice. Defaults to "
             "the sum of the order line quantities and can be overridden.",
    )

    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        sale_order_id = (
            res.get("sale_order_id")
            or self.env.context.get("default_sale_order_id")
        )

        if sale_order_id:
            order = self.env["sale.order"].browse(sale_order_id)

            lines = order.order_line.filtered(
                lambda l: not l.display_type and not l.is_downpayment
            )

            full_total = sum(lines.mapped("price_total"))
            total_qty = sum(lines.mapped("product_uom_qty"))

            if "summary" in fields_list:
                res["summary"] = order._get_auto_summary_description()

            if "full_amount" in fields_list:
                res["full_amount"] = full_total

            if "amount" in fields_list:
                res["amount"] = full_total

            if "qty" in fields_list:
                res["qty"] = total_qty

            if "payment_percentage" in fields_list:
                res["payment_percentage"] = "custom"

        return res

    @api.onchange("payment_percentage")
    def _onchange_payment_percentage(self):
        if self.payment_percentage == "custom":
            return

        percentage = float(self.payment_percentage) / 100.0
        self.amount = self.full_amount * percentage

    def action_print_report(self):
        self.ensure_one()

        # Pass wizard values to the Sale Order
        self.sale_order_id.write({
            "pi_summary_override": self.summary,
            "pi_amount_override": self.amount,
            "pi_qty_override": self.qty,
        })

        # Log this PI generation to history
        self.env["sale.order.pi.history"].create({
            "sale_order_id": self.sale_order_id.id,
            "name": self.sale_order_id._get_next_pi_name(),
            "summary": self.summary,
            "full_amount": self.full_amount,
            "amount": self.amount,
            "qty": self.qty,
            "payment_percentage": self.payment_percentage,
        })

        report_action = self.env.ref(
            "wood_world_customistation.action_report_sale_order_simplified"
        ).report_action(self.sale_order_id)

        report_action["close_on_report_download"] = True

        return report_action