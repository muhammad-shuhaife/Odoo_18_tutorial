# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    custom_image_1 = fields.Image(
        string="Picture",
        max_width=1024,
        max_height=1024,
        help="Custom picture for this quotation line. If left empty, "
             "the product's own image will be used instead.",
    )

    report_image_1 = fields.Image(
        string="Picture",
        compute="_compute_report_images",
        compute_sudo=True,
        store=False,
    )

    @api.depends("custom_image_1", "product_id", "product_id.image_128")
    def _compute_report_images(self):
        for line in self:
            line.report_image_1 = line.custom_image_1 or (
                line.product_id.image_128 if line.product_id else False
            )
