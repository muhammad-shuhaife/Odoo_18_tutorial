# -*- coding: utf-8 -*-
{
    'name': "Wood World Decor - Sale Customization",
    'summary': "Custom Proforma Invoice report and summary wizard for Sale Orders",
    'description': """
Wood World Decor Sale Order Customization
==========================================

This module extends Sale Orders for Wood World Decor L.L.C. with:

* A simplified Proforma Invoice (PI) PDF report with custom letterhead,
  aggregated product summary line, and amount-in-words.
* A wizard to review order lines and manually edit the summary description
  shown on the printed Proforma Invoice before printing.
    """,
    'author': "Muhammad Shuhaife",
    'category': 'Sales/Sales',
    'version': '1.2.30',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale',
        'purchase',
        'account',
        'sale_project',
        'project',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/sale_pi_report.xml',
        'report/quotation_report.xml',
        'report/purchase_order_report.xml',
        'report/customer_invoice_report.xml',
        'wizard/sale_order_pi_summary_wizard_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/res_compny_views.xml',
        'views/account_move_views.xml',
        'views/sale_order_pi_history.xml',
    ],
    'demo': [],
    'assets': {},
    'icon': 'wood_world_customistation/static/src/img/logo.jpg',
    'installable': True,
    'application': False,
    'auto_install': False,
}
